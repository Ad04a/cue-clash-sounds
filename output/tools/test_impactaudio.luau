-- Headless check of roblox/ImpactAudio.luau with Lune: mocks the few Roblox APIs it
-- touches, replays a simulated break frame by frame and counts what would play.
-- usage (from the game repo, where lune is pinned):
--   lune run ../ball-hit-sounds/output/tools/test_impactaudio.luau <events.json> <ImpactAtlas.luau path>

local fs = require("@lune/fs")
local serde = require("@lune/serde")
local process = require("@lune/process")
local task = require("@lune/task")

local now = 0
local played = {}

local function newInstance(class)
	local inst = { ClassName = class, Volume = 0.5, PlaybackSpeed = 1 }
	inst.Ended = {
		Once = function() end,
	}
	function inst:Clone()
		local c = newInstance(class)
		for k, v in self do
			if c[k] == nil then
				c[k] = v
			end
		end
		return c
	end
	function inst:Destroy() end
	function inst:Play()
		table.insert(played, {
			t = now,
			id = self.SoundId,
			volume = self.Volume,
			pitch = self.PlaybackSpeed,
			region = self.PlaybackRegion,
		})
	end
	return inst
end

-- Roblox globals used by the module
_G.game = {
	GetService = function()
		return newInstance("SoundService")
	end,
}
local seed = 12345
local function rand()
	seed = (seed * 1103515245 + 12345) % 2147483648
	return seed / 2147483648
end
local Random = {
	new = function()
		return {
			NextNumber = function(_, a, b)
				if a then
					return a + (b - a) * rand()
				end
				return rand()
			end,
			NextInteger = function(_, a, b)
				return a + math.floor(rand() * (b - a + 1))
			end,
		}
	end,
}
-- voice cleanup timers run on simulated time, not wall clock
local timers = {}
local simTask = {
	defer = task.defer,
	delay = function(dt, fn)
		table.insert(timers, { at = now + dt, fn = fn })
	end,
}
local function runTimers()
	local keep = {}
	for _, tm in timers do
		if tm.at <= now then
			tm.fn()
		else
			table.insert(keep, tm)
		end
	end
	timers = keep
end
local env = {
	game = _G.game,
	Instance = { new = newInstance },
	Random = Random,
	NumberRange = {
		new = function(a, b)
			return { Min = a, Max = b }
		end,
	},
	Enum = { RollOffMode = { InverseTapered = "InverseTapered" } },
	workspace = { Terrain = newInstance("Terrain") },
	task = simTask,
	os = {
		clock = function()
			return now
		end,
	},
}

local function load(path)
	local src = fs.readFile(path)
	local chunk = assert(loadstring(src, "=" .. path))
	setfenv(chunk, setmetatable(env, { __index = getfenv(1) }))
	return chunk()
end

local eventsPath, atlasPath = process.args[1], process.args[2]
local ImpactAudio = load(string.gsub(atlasPath, "ImpactAtlas", "ImpactAudio"))
local regions = load(atlasPath)
ImpactAudio.init(ImpactAudio.bankFromAtlas(regions.hybrid, "rbxassetid://ATLAS"))

local events = serde.decode("json", fs.readFile(eventsPath))
local FRAME = 1 / 60
local i, n = 1, #events
local nBall = 0
while i <= n do
	local ft = math.floor(events[i].t / FRAME) * FRAME + FRAME
	now = ft
	runTimers()
	while i <= n and events[i].t < ft do
		local e = events[i]
		if e.kind ~= "pocket" then
			ImpactAudio.push({ kind = e.kind, speed = e.speed })
		end
		if e.kind == "ball" then
			nBall += 1
		end
		i += 1
	end
	task.wait() -- lets the deferred flush run, like the end of a Roblox frame
end
task.wait()

-- which folder did each voice come from? (map region start back to the atlas table)
local folderOf = {}
for folder, layers in regions.hybrid do
	for _, list in layers do
		for _, r in list do
			folderOf[r.start] = folder
		end
	end
end
local counts, loud = {}, 0
for _, p in played do
	local f = folderOf[p.region.Min] or "?"
	counts[f] = (counts[f] or 0) + 1
	loud = math.max(loud, p.volume)
end
print(string.format("ball events %d -> voices %d (max volume %.2f)", nBall, #played, loud))
for f, c in counts do
	print("  ", f, c)
end
