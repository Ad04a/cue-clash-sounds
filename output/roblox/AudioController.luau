--!strict
-- Shot sounds and haptics driven by simulation events.
-- Cue / ball / rail impacts go through ImpactAudio (velocity layers, voice budget,
-- break clustering); everything else still uses the simple PoolConfig.Sounds ids.
--
-- Drop-in replacement for StarterPlayer/StarterPlayerScripts/Client/Controllers/AudioController.luau
-- once ImpactAudio.luau and ImpactAtlas.luau are in ReplicatedStorage/Shared/Audio/ and
-- PoolConfig.ImpactAtlas holds the uploaded atlas id.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local PoolConfig = require(Shared.Config.PoolConfig)
local Simulation = require(Shared.Pool.Simulation)
local ImpactAudio = require(Shared.Audio.ImpactAudio)
local ImpactAtlas = require(Shared.Audio.ImpactAtlas)

local TableController = require(script.Parent.TableController)

local AudioController = {}

local MAX_SPEED = PoolConfig.Physics.MaxShotSpeed

local templates: { [string]: Sound } = {}

local function load()
	local folder = Instance.new("Folder")
	folder.Name = "PoolSounds"
	for name: string, id: string in PoolConfig.Sounds :: { [string]: string } do
		if id ~= "" then
			local s = Instance.new("Sound")
			s.Name = name
			s.SoundId = id
			s.Parent = folder
			templates[name] = s
		end
	end
	folder.Parent = SoundService

	local atlas = (PoolConfig :: any).ImpactAtlas :: { Id: string, Bank: string }?
	if atlas and atlas.Id ~= "" then
		ImpactAudio.init(ImpactAudio.bankFromAtlas((ImpactAtlas :: any)[atlas.Bank], atlas.Id))
	end

	local music = PoolConfig.Music
	if music.Id ~= "" then
		local m = Instance.new("Sound")
		m.Name = "BackgroundMusic"
		m.SoundId = music.Id
		m.Volume = music.Volume
		m.Looped = true
		m.Parent = SoundService
		m:Play()
	end
end

function AudioController.play(name: string, volume: number?, pitch: number?)
	local template = templates[name]
	if not template then
		return
	end
	local s = template:Clone()
	s.Volume = volume or 0.5
	s.PlaybackSpeed = pitch or 1
	s.Parent = template.Parent
	s.Ended:Once(function()
		s:Destroy()
	end)
	s:Play()
end

-- Light haptic pulse on supported mobile devices (guarded: API availability varies)
local hapticEffect: Instance? = nil
local function haptic(strength: number)
	if not UserInputService.TouchEnabled then
		return
	end
	if hapticEffect == nil then
		local ok, effect = pcall(function()
			local e = Instance.new("HapticEffect")
			e.Parent = SoundService
			return e
		end)
		hapticEffect = if ok then effect else false :: any
	end
	if hapticEffect then
		pcall(function()
			local e = hapticEffect :: any
			e.Type = if strength > 0.6
				then Enum.HapticEffectType.GameplayExplosion
				else Enum.HapticEffectType.GameplayCollision
			e:Play()
		end)
	end
end

local function onEvent(e: Simulation.Event)
	if e.kind == "cue" or e.kind == "ball" or e.kind == "cushion" or e.kind == "bounce" then
		ImpactAudio.push({ kind = e.kind, speed = e.speed })
		if e.kind == "cue" then
			haptic(math.clamp(e.speed / (MAX_SPEED * 0.6), 0, 1))
		end
	elseif e.kind == "pocket" then
		AudioController.play("Pocket", 3, 1)
		haptic(0.4)
	end
end

function AudioController.start()
	load()
	TableController.SimEvent:Connect(onEvent)
end

return AudioController
