-- Headless check of roblox/GameSounds.luau with Lune (mocked Roblox APIs).
-- usage (from the game repo, where lune is pinned):
--   lune run ../ball-hit-sounds/output/tools/test_gamesounds.luau ../ball-hit-sounds/output/roblox

local fs = require("@lune/fs")
local process = require("@lune/process")
local task = require("@lune/task")

local dir = process.args[1]
local played = {}

local function newInstance(class)
	local inst = { ClassName = class, Volume = 0.5, PlaybackSpeed = 1, Looped = false }
	inst.Ended = { Once = function() end }
	function inst:Destroy()
		inst.Destroyed = true
	end
	function inst:Play()
		table.insert(played, inst)
	end
	return inst
end

local function load(path, env)
	local chunk = assert(loadstring(fs.readFile(path), "=" .. path))
	setfenv(chunk, setmetatable(env, { __index = getfenv(1) }))
	return chunk()
end

local seed = 7
local Random = {
	new = function()
		return {
			NextInteger = function(_, a, b)
				seed = (seed * 1103515245 + 12345) % 2147483648
				return a + seed % (b - a + 1)
			end,
		}
	end,
}

local atlas = load(dir .. "/GameSoundAtlas.luau", {})
local env = {
	game = {
		GetService = function(_, name)
			if name == "ContentProvider" then
				return { PreloadAsync = function() end }
			end
			return newInstance(name)
		end,
	},
	Instance = { new = newInstance },
	Random = Random,
	NumberRange = {
		new = function(a, b)
			return { Min = a, Max = b }
		end,
	},
	Enum = { RollOffMode = { InverseTapered = "InverseTapered" } },
	task = { spawn = task.spawn, delay = function() end, defer = task.defer },
	script = { Parent = { GameSoundAtlas = "ATLAS" } },
	require = function(x)
		assert(x == "ATLAS")
		return atlas
	end,
}
local GameSounds = load(dir .. "/GameSounds.luau", env)

local fails = 0
local function check(ok, msg)
	if not ok then
		fails += 1
		print("FAIL: " .. msg)
	end
end

-- before init: nothing plays
check(GameSounds.play("button_click") == nil, "play before init should return nil")

local loopIds = {}
for name in atlas.loops do
	loopIds[name] = "rbxassetid://loop_" .. name
end
GameSounds.init(
	{ ui = "rbxassetid://ui", machine = "rbxassetid://machine", game = "rbxassetid://game" },
	loopIds
)

local maxEnd = {}
local count = 0
for name, entry in atlas.sounds do
	for _ = 1, 3 do
		local s = GameSounds.play(name)
		check(s ~= nil, "play returned nil for " .. name)
		if s then
			check(s.SoundId == "rbxassetid://" .. entry.atlas, name .. ": wrong atlas id")
			check(s.PlaybackRegionsEnabled == true, name .. ": regions not enabled")
			local r = s.PlaybackRegion
			check(r.Max > r.Min and r.Min >= 0, name .. ": bad region")
			maxEnd[entry.atlas] = math.max(maxEnd[entry.atlas] or 0, r.Max)
		end
	end
	count += 1
end

-- variants never repeat back to back
local prev = nil
for _ = 1, 40 do
	local s = GameSounds.play("button_click")
	local key = s and s.PlaybackRegion.Min
	check(key ~= prev, "button_click repeated the same variant twice in a row")
	prev = key
end

check(GameSounds.play("no_such_sound") == nil, "unknown name should return nil")
check(GameSounds.play("button_click", { variant = 99 }) ~= nil, "variant out of range should clamp")
local s3d = GameSounds.play("token_insert", { parent = newInstance("Part") })
check(s3d ~= nil and s3d.RollOffMode == "InverseTapered", "3D play should set roll-off")

local nloops = 0
for name in atlas.loops do
	local l = GameSounds.loop(name)
	check(l ~= nil and l.Looped == true, "loop failed for " .. name)
	check(GameSounds.has(name), "has() false for loop " .. name)
	nloops += 1
end
check(GameSounds.loop("button_click") == nil, "one-shot name should not start a loop")
check(GameSounds.has("reveal_mythic"), "has() false for reveal_mythic")

print(string.format("%d one-shots, %d loops, %d plays", count, nloops, #played))
for a, e in maxEnd do
	print(string.format("  %s atlas: last region ends at %.2f s", a, e))
end
print(if fails == 0 then "ALL CHECKS PASSED" else (fails .. " CHECK(S) FAILED"))
