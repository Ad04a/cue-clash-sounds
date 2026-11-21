--!strict
-- GameSounds: plays Cue Clash's UI, ball-machine and game-event sounds by name.
--
-- The one-shots live in three uploaded atlases (ui_atlas.ogg, machine_atlas.ogg,
-- game_atlas.ogg); GameSoundAtlas.luau says where each sound sits. Loops are uploaded
-- as separate files.
--
--   GameSounds.init({ ui = "rbxassetid://..", machine = "rbxassetid://..", game = "rbxassetid://.." },
--       { pool_hall_ambience_loop = "rbxassetid://..", ... })
--   GameSounds.play("button_click")
--   GameSounds.play("rack_place_ball", { volume = 0.7 })
--   GameSounds.play("select_note_1", { pitch = 1.05 })
--   GameSounds.play("token_insert", { parent = machinePart })  -- 3D, from the machine
--   local hum = GameSounds.loop("pool_hall_ambience_loop", { volume = 0.3 }); hum:Stop()

local ContentProvider = game:GetService("ContentProvider")
local SoundService = game:GetService("SoundService")

local GameSoundAtlas = require(script.Parent.GameSoundAtlas)

export type PlayOptions = {
	volume: number?, -- default: GameSounds.Volume[atlas]
	pitch: number?, -- PlaybackSpeed
	variant: number?, -- pick a specific variant (1..n); default: random, never the same twice in a row
	parent: Instance?, -- e.g. a Part or Attachment for a 3D sound; default: SoundService folder
}

local GameSounds = {}

-- Default volume per atlas. The files are mastered so one value per atlas works:
-- hovers are quieter than clicks, which are quieter than the big stingers, on purpose.
GameSounds.Volume = { ui = 0.5, machine = 0.6, game = 0.6, loop = 0.4 } :: { [string]: number }
GameSounds.RollOff = { min = 8, max = 60 } -- for sounds parented to a part

local atlasIds: { [string]: string } = {}
local loopIds: { [string]: string } = {}
local lastVariant: { [string]: number } = {}
local rng = Random.new()
local folder: Folder? = nil

function GameSounds.init(atlases: { [string]: string }, loops: { [string]: string }?)
	atlasIds = atlases
	loopIds = loops or {}
	local f = Instance.new("Folder")
	f.Name = "GameSounds"
	f.Parent = SoundService
	folder = f
	-- preload the atlases so the first click isn't silent
	local preload = {}
	for name, id in atlasIds do
		if id ~= "" then
			local s = Instance.new("Sound")
			s.Name = name .. "_atlas"
			s.SoundId = id
			s.Parent = f
			table.insert(preload, s)
		end
	end
	task.spawn(function()
		pcall(function()
			ContentProvider:PreloadAsync(preload)
		end)
	end)
end

function GameSounds.has(name: string): boolean
	local entry = GameSoundAtlas.sounds[name]
	if entry then
		return (atlasIds[entry.atlas] or "") ~= ""
	end
	return (loopIds[name] or "") ~= ""
end

local function pickVariant(name: string, n: number): number
	local v = rng:NextInteger(1, n)
	if n > 1 and v == lastVariant[name] then
		v = v % n + 1
	end
	lastVariant[name] = v
	return v
end

local function place(s: Sound, parent: Instance?)
	if parent then
		s.RollOffMode = Enum.RollOffMode.InverseTapered
		s.RollOffMinDistance = GameSounds.RollOff.min
		s.RollOffMaxDistance = GameSounds.RollOff.max
		s.Parent = parent
	else
		s.Parent = folder or SoundService
	end
end

-- Play a one-shot by name. Returns the Sound (already playing), or nil if the name or
-- its atlas id is unknown. The Sound cleans itself up.
function GameSounds.play(name: string, opts: PlayOptions?): Sound?
	local o: PlayOptions = opts or {}
	local entry = GameSoundAtlas.sounds[name]
	if not entry then
		return nil
	end
	local id = atlasIds[entry.atlas]
	if not id or id == "" then
		return nil
	end
	local n = #entry.regions
	local v = if o.variant then math.clamp(o.variant, 1, n) else pickVariant(name, n)
	local r = entry.regions[v]
	local pitch = o.pitch or 1
	local s = Instance.new("Sound")
	s.Name = name
	s.SoundId = id
	s.Volume = o.volume or GameSounds.Volume[entry.atlas] or 0.5
	s.PlaybackSpeed = pitch
	s.PlaybackRegionsEnabled = true
	s.PlaybackRegion = NumberRange.new(r.start, r.start + r.length)
	s.TimePosition = r.start
	place(s, o.parent)
	local done = false
	local function cleanup()
		if not done then
			done = true
			s:Destroy()
		end
	end
	s.Ended:Once(cleanup)
	task.delay(r.length / pitch + 0.5, cleanup) -- in case Ended doesn't fire at a region's end
	s:Play()
	return s
end

-- Start a looping sound (ambience, crank, globe rattle, coin counter). The caller owns it:
-- call :Stop() / :Destroy() when done.
function GameSounds.loop(name: string, opts: PlayOptions?): Sound?
	local o: PlayOptions = opts or {}
	local id = loopIds[name]
	if not id or id == "" then
		return nil
	end
	local s = Instance.new("Sound")
	s.Name = name
	s.SoundId = id
	s.Looped = true
	s.Volume = o.volume or GameSounds.Volume.loop
	s.PlaybackSpeed = o.pitch or 1
	place(s, o.parent)
	s:Play()
	return s
end

return GameSounds
