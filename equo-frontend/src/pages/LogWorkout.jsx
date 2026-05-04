// src/pages/LogWorkout.jsx

import { useState } from "react"
import { logWorkout } from "../api/equo"

const USER_ID = 1
const ACTIVITIES = [
    // cardio
    "running", "jogging",  "walking", "hiking", "cycling", "swimming",
    "rowing", "elliptical", "jump rope", "stair climbing",

    // strength
    "weightlifting", "bodyweight", "crossfit", "powerlifting",

    // classes
    "hiit", "yoga", "pilates", "stretching",

    // sports
    "boxing", "basketball", "soccer", "tennis", "volleyball", "golf",
    "dance", "martial arts", "rock climbing", "pickleball"
]

export default function LogWorkout() {
    const [activity, setActivity] = useState("running")
    const [duration, setDuration] = useState("")
    const [override, setOverride] = useState("")
    const [logged, setLogged] = useState(false)

    const handleLog = async () => {
        await logWorkout(USER_ID, activity, parseInt(duration), override ? parseFloat(override) : null)
        setLogged(true)
    }

    if (logged) return (
        <div className="max-w-lg mx-auto p-6 text-center space-y-4">
            <p className="text-2xl">✓</p>
            <p className="font-semibold">Workout logged</p>
            <a href="/" className="text-blue-500 text-sm">Back to dashboard</a>
        </div>
    )

    return (
        <div className="max-w-lg mx-auto p-6 space-y-6">
            <div className="flex items-center gap-3">
                <a href="/" className="text-gray-400">←</a>
                <h1 className="text-xl font-bold">Log a workout</h1>
            </div>

            {/* activity */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Activity</label>
                <select
                    className="w-full border rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    value={activity}
                    onChange={e => setActivity(e.target.value)}
                >
                    {ACTIVITIES.map(a => (
                        <option key={a} value={a} className="capitalize">{a}</option>
                    ))}
                </select>
            </div>

            {/* duration */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Duration (minutes)</label>
                <input
                    type="number"
                    className="w-full border rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="30"
                    value={duration}
                    onChange={e => setDuration(e.target.value)}
                />
            </div>

            {/* override */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                    Calories burned <span className="text-gray-400 font-normal">(optional - from fitness tracker)</span>
                </label>
                <input
                    type="number"
                    className="w-full border rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="Leave blank to calculate automatically"
                    value={override}
                    onChange={e => setOverride(e.target.value)}
                />
            </div>

            <button
                onClick={handleLog}
                disabled={!activity || !duration}
                className="w-full bg-blue-500 text-white py-3 rounded-xl font-semibold disabled:opacity-40"
            >
                Log workout
            </button>
        </div>
    )
}