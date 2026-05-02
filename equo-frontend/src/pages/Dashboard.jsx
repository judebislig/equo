// src/pages/Dashboard.jsx
import { useState, useEffect } from "react"
import { getToday, getTodaysMeals, getTodaysWorkouts } from "../api/equo"

const USER_ID = 1 // hardcoded for now

export default function Dashboard() {
    const [summary, setSummary] = useState(null)
    const [meals, setMeals] = useState([])
    const [workouts, setWorkouts] = useState([])

    // Fetches data once in the component when the page loads
    useEffect(() => {
        getToday(USER_ID).then(setSummary)
        getTodaysMeals(USER_ID).then(setMeals).catch(() => setMeals([]))
        getTodaysWorkouts(USER_ID).then(setWorkouts).catch(() => setWorkouts([]))
    }, [])

    if (!summary) return <div className="p-8 text-gray-500">Loading...</div>

    const caloriePercent = Math.min((summary.calories_eaten / summary.calorie_target) * 100, 100)

    return (
        <div className="flex justify-between items-center">
            <h1 className="text-2x1 font-bold">Equo</h1>
        </div>
    )
}