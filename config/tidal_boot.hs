:set -XOverloadedStrings
:set prompt ""
import Sound.Tidal.Context
tidal <- startTidal (superdirtTarget {oLatency = 0.05}) (defaultConfig {cVerbose = True})
let p = streamReplace tidal
let hush = streamHush tidal
let d1 = p 1
let d2 = p 2
let d3 = p 3
let d4 = p 4
let d5 = p 5
let d6 = p 6
:set prompt "tidal> "
