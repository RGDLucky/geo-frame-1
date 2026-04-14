import { useState, useEffect } from "react"
import { ComposableMap, Geographies, Geography, Sphere, Graticule, Marker } from "react-simple-maps"

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"

interface Coordinate {
    id: string;
    name: string;
    lat: number;
    lng: number;
    info?: string;
}

function App() {
    const [coordinates, setCoordinates] = useState<Coordinate[]>([])
    const [selectedCoord, setSelectedCoord] = useState<Coordinate | null>(null)

    useEffect(() => {
        fetch("/api/coordinates")
            .then(res => res.json())
            .then(data => setCoordinates(data))
            .catch(err => console.error("Failed to load coordinates:", err))
    }, [])

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-900 relative">
            <ComposableMap
                projection="geoMercator"
                projectionConfig={{
                    rotate: [0, 0, 0],
                    center: [0, 20],
                    // scale: 147
                    scale: 120
                }}
                className="w-full h-full max-w-6xl"
            >
                <Sphere stroke="#334155" />
                <Graticule stroke="#334155" />
                <Geographies geography={geoUrl}>
                    {({ geographies }) =>
                        geographies.map((geo) => (
                            <Geography
                                key={geo.rsmKey}
                                geography={geo}
                                fill="#1e293b"
                                stroke="#334155"
                                strokeWidth={0.5}
                                style={{
                                    default: { outline: "none" },
                                    hover: { fill: "#3b82f6", outline: "none" },
                                    pressed: { fill: "#2563eb", outline: "none" }
                                }}
                            />
                        ))
                    }
                </Geographies>
                {coordinates.map((coord) => (
                    <Marker
                        key={coord.id}
                        coordinates={[coord.lng, coord.lat]}
                        onClick={() => setSelectedCoord(coord)}
                        style={{
                            default: { fill: "#f59e0b", cursor: "pointer" },
                            hover: { fill: "#fbbf24", cursor: "pointer" },
                            pressed: { fill: "#d97706" }
                        }}
                    >
                        <circle r={4} cx={0} cy={0} />
                    </Marker>
                ))}
            </ComposableMap>

            {selectedCoord && (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-xl max-w-xs z-10">
                    <h3 className="text-lg font-bold text-white mb-2">{selectedCoord.name}</h3>
                    <p className="text-gray-300 text-sm mb-4">{selectedCoord.info}</p>
                    <button
                        onClick={() => setSelectedCoord(null)}
                        className="text-sm text-blue-400 hover:text-blue-300"
                    >
                        Close
                    </button>
                </div>
            )}
        </div>
    )
}

export default App
