--!strict
-- ImpactAudio: billiard impact sounds (cue strike, ball-ball, rail) driven by the
-- simulation's events, with a voice budget that keeps a 40-contact break sounding
-- like one powerful crash instead of a machine gun.
--
-- Same rules as ball-hit-sounds/output/tools/impactmix.py (used to render the
-- break previews), so what you hear in break_renders/ is what this plays.
--
--   per event : intensity k = speed / vref  ->  volume = vmax * k^curve
--               layer soft/medium/hard by k (dithered near the edges)
--               round-robin variant, small random pitch
--   per frame : the loudest events get their own voice (budget per kind per window);
--               the energy of the rest is summed (sqrt of sum of squares, as for
--               incoherent sources) and played as ONE multi-ball "cluster" sample;
--               a loudness guard divides every volume by sqrt(1 + recentEnergy / E0)

local SoundService = game:GetService("SoundService")

export type Clip = { id: string, start: number?, length: number? } -- start/length: slice of an atlas
export type Layers = { soft: { Clip }, medium: { Clip }, hard: { Clip } }
export type Bank = { [string]: Layers } -- folders: cue, ball, rail, table, cluster
export type Region = { start: number, length: number }
export type ImpactEvent = { kind: string, speed: number, position: Vector3? }

type KindConfig = { vref: number, curve: number, vmax: number, folder: string }

local ImpactAudio = {}

ImpactAudio.Config = {
	MasterVolume = 1.0,
	KMin = 0.012, -- quieter than this is not played at all
	Kinds = {
		-- vref: speed (studs/s) that counts as a full-power hit for this kind
		cue = { vref = 25, curve = 1.0, vmax = 1.0, folder = "cue" },
		ball = { vref = 16, curve = 1.2, vmax = 0.9, folder = "ball" },
		cushion = { vref = 12, curve = 1.3, vmax = 0.8, folder = "rail" },
		bounce = { vref = 6, curve = 1.3, vmax = 0.45, folder = "table" }, -- ball landing on the cloth
	} :: { [string]: KindConfig },
	LayerEdges = { 0.22, 0.55 },
	LayerDither = 0.06,
	PitchJitter = 0.02,
	VolumeJitter = 0.12, -- +-12 % per hit: no two hits exactly alike
	PitchBySpeed = 0.03,
	Window = 0.08, -- seconds the voice budget counts over
	Budget = { ball = 6, cushion = 3, bounce = 2, cue = 2 } :: { [string]: number },
	ChatterGain = 0.8,
	ChatterMinInterval = 0.03,
	LoudnessE0 = 1.6,
	LoudnessTau = 0.06,
	MaxLiveVoices = 24, -- hard cap on Sounds alive at once
	RollOff = { min = 6, max = 80 }, -- only used for events that carry a position
	-- Light diffuse room (a ReverbSoundEffect on the impact SoundGroup). The hits
	-- themselves are dry, like a close mic; this puts them in a room. Off: Enabled = false.
	Room = { Enabled = true, DecayTime = 0.6, Density = 1, Diffusion = 1, DryLevel = 0, WetLevel = -17 },
}

local LAYERS = { "soft", "medium", "hard" }

local bank: Bank? = nil
local rng = Random.new()
local folderInst: Folder? = nil
local group: SoundGroup? = nil
local templates: { [string]: Sound } = {}
local lastVariant: { [string]: number } = {}
local voices: { { t: number, kind: string } } = {}
local energy, energyT = 0, 0
local lastChatter = -1
local live = 0
local queue: { ImpactEvent } = {}
local flushScheduled = false

-- Build a Bank from ImpactAtlas.luau regions and the uploaded atlas asset id.
function ImpactAudio.bankFromAtlas(regions: { [string]: { [string]: { Region } } }, atlasId: string): Bank
	local out: Bank = {}
	for folder, layers in regions do
		local l = {} :: any
		for layer, list in layers do
			local clips = {}
			for _, r in list do
				table.insert(clips, { id = atlasId, start = r.start, length = r.length })
			end
			l[layer] = clips
		end
		out[folder] = l
	end
	return out
end

-- Build a Bank from individually uploaded files: ids[folder][layer] = { "rbxassetid://..", .. }
function ImpactAudio.bankFromIds(ids: { [string]: { [string]: { string } } }): Bank
	local out: Bank = {}
	for folder, layers in ids do
		local l = {} :: any
		for layer, list in layers do
			local clips = {}
			for _, id in list do
				if id ~= "" then
					table.insert(clips, { id = id })
				end
			end
			l[layer] = clips
		end
		out[folder] = l
	end
	return out
end

function ImpactAudio.init(b: Bank, parent: Instance?)
	bank = b
	local f = Instance.new("Folder")
	f.Name = "ImpactSounds"
	f.Parent = parent or SoundService
	folderInst = f
	local g = Instance.new("SoundGroup")
	g.Name = "ImpactSoundGroup"
	g.Parent = SoundService
	local room = ImpactAudio.Config.Room
	if room.Enabled then
		local r = Instance.new("ReverbSoundEffect")
		r.DecayTime = room.DecayTime
		r.Density = room.Density
		r.Diffusion = room.Diffusion
		r.DryLevel = room.DryLevel
		r.WetLevel = room.WetLevel
		r.Parent = g
	end
	group = g
end

local function gauss(): number
	local u1 = math.max(rng:NextNumber(), 1e-6)
	return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * rng:NextNumber())
end

local function pickLayer(k: number): string
	local c = ImpactAudio.Config
	local kd = k + rng:NextNumber(-c.LayerDither, c.LayerDither)
	if kd < c.LayerEdges[1] then
		return "soft"
	elseif kd < c.LayerEdges[2] then
		return "medium"
	end
	return "hard"
end

local function clipsFor(folder: string, layer: string): { Clip }?
	local layers = bank and (bank :: Bank)[folder]
	if not layers then
		return nil
	end
	local list = (layers :: any)[layer] :: { Clip }?
	if list and #list > 0 then
		return list
	end
	for _, other in LAYERS do -- missing layer: fall back to any layer that has clips
		local alt = (layers :: any)[other] :: { Clip }?
		if alt and #alt > 0 then
			return alt
		end
	end
	return nil
end

local function pickVariant(key: string, n: number): number
	local v = rng:NextInteger(1, n)
	if n > 1 and v == lastVariant[key] then
		v = (v + rng:NextInteger(0, n - 2)) % n + 1
	end
	lastVariant[key] = v
	return v
end

local function guard(now: number, g: number): number
	local c = ImpactAudio.Config
	energy *= math.exp(-(now - energyT) / c.LoudnessTau)
	energyT = now
	g /= math.sqrt(1 + energy / c.LoudnessE0)
	energy += g * g
	return g
end

local function template(id: string): Sound
	local existing = templates[id]
	if existing then
		return existing
	end
	local t = Instance.new("Sound")
	t.SoundId = id
	t.SoundGroup = group
	t.Parent = folderInst
	templates[id] = t
	return t
end

local function spawnVoice(clip: Clip, volume: number, pitch: number, position: Vector3?)
	if live >= ImpactAudio.Config.MaxLiveVoices then
		return
	end
	local s = template(clip.id):Clone()
	s.Volume = volume * ImpactAudio.Config.MasterVolume
	s.PlaybackSpeed = pitch
	if clip.start then
		s.PlaybackRegionsEnabled = true
		s.PlaybackRegion = NumberRange.new(clip.start, clip.start + (clip.length or 0.5))
		s.TimePosition = clip.start
	end
	local holder: Instance = folderInst :: Folder
	if position then
		local a = Instance.new("Attachment")
		a.WorldPosition = position
		a.Parent = workspace.Terrain
		s.RollOffMode = Enum.RollOffMode.InverseTapered
		s.RollOffMinDistance = ImpactAudio.Config.RollOff.min
		s.RollOffMaxDistance = ImpactAudio.Config.RollOff.max
		holder = a
	end
	s.Parent = holder
	live += 1
	local done = false
	local function cleanup()
		if done then
			return
		end
		done = true
		live -= 1
		if holder ~= folderInst then
			holder:Destroy()
		else
			s:Destroy()
		end
	end
	s.Ended:Once(cleanup)
	task.delay((clip.length or 1.5) / pitch + 0.25, cleanup) -- in case Ended doesn't fire for a region
	s:Play()
end

local function emit(now: number, folder: string, k: number, g: number, position: Vector3?)
	local layer = pickLayer(k)
	local list = clipsFor(folder, layer)
	if not list then
		return
	end
	local c = ImpactAudio.Config
	local clip = list[pickVariant(folder .. layer, #list)]
	local j = math.clamp(gauss() * c.PitchJitter, -0.045, 0.045)
	g *= 1 + rng:NextNumber(-c.VolumeJitter, c.VolumeJitter)
	spawnVoice(clip, guard(now, g), 1 + j + c.PitchBySpeed * (k - 0.5), position)
end

local function flush()
	flushScheduled = false
	local batch = queue
	queue = {}
	local c = ImpactAudio.Config
	local now = os.clock()
	local kept = {}
	for _, v in voices do
		if now - v.t < c.Window then
			table.insert(kept, v)
		end
	end
	voices = kept

	local scored: { { g: number, k: number, e: ImpactEvent } } = {}
	for _, e in batch do
		local kc = c.Kinds[e.kind]
		if kc then
			local k = math.clamp(e.speed / kc.vref, 0, 1)
			if k >= c.KMin then
				table.insert(scored, { g = kc.vmax * k ^ kc.curve, k = k, e = e })
			end
		end
	end
	table.sort(scored, function(a, b)
		return a.g > b.g
	end)

	local poolE, poolN = 0, 0
	local poolPos: Vector3? = nil
	for _, s in scored do
		local kind = s.e.kind
		local used = 0
		for _, v in voices do
			if v.kind == kind then
				used += 1
			end
		end
		if used < (c.Budget[kind] or 4) then
			table.insert(voices, { t = now, kind = kind })
			emit(now, c.Kinds[kind].folder, s.k, s.g, s.e.position)
		elseif kind == "ball" then
			poolE += s.g * s.g
			poolN += 1
			poolPos = poolPos or s.e.position
		end
		-- over-budget rail/bounce hits are masked by the louder ones: dropped
	end
	if poolN > 0 and now - lastChatter >= c.ChatterMinInterval then
		lastChatter = now
		local meanK = (math.sqrt(poolE / poolN) / c.Kinds.ball.vmax) ^ (1 / 1.2)
		emit(now, "cluster", meanK, math.min(c.ChatterGain * math.sqrt(poolE), 1), poolPos)
	end
end

-- Queue one simulation event ({ kind, speed, position? }). Everything queued during a
-- frame is mixed together once, right after the current frame's events have fired.
function ImpactAudio.push(e: ImpactEvent)
	if not bank or not ImpactAudio.Config.Kinds[e.kind] then
		return
	end
	table.insert(queue, e)
	if not flushScheduled then
		flushScheduled = true
		task.defer(flush)
	end
end

return ImpactAudio
