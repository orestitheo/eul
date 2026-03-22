// SuperDirt boot — auto-loaded from ~/.config/SuperCollider/startup.scd
// Loads all sample banks from /opt/eul/samples/
// Each subfolder becomes a named bank in TidalCycles (e.g. sound "glitch1")

s.options.numBuffers = 1024 * 16;
s.options.memSize = 8192 * 16;
s.options.numWireBufs = 64;
s.options.maxNodes = 1024 * 32;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 2;

s.waitForBoot {
    ~dirt = SuperDirt(2, s);
    ~dirt.loadSoundFiles("/opt/eul/samples/drone");
    ~dirt.loadSoundFiles("/opt/eul/samples/texture");
    ~dirt.loadSoundFiles("/opt/eul/samples/percussive/dungeondrums");
    ~dirt.loadSoundFiles("/opt/eul/samples/percussive/rad");
    ~dirt.loadSoundFiles("/opt/eul/samples/percussive/shxc1");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/chords/ls");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/chords/discoveryone");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/chords/akatosh_chord");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/chords/blackmirror");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/chords/shxc");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/chords/t99");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/singletone/discoveryone");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/singletone/akatosh_voice");
    ~dirt.loadSoundFiles("/opt/eul/samples/melodic/singletone/madonna");
    ~dirt.start(57120, [0, 0]);
    "SuperDirt ready".postln;
};
