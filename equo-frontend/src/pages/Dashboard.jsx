// src/pages/Dashboard.jsx
import { useState, useEffect } from "react"
import { getToday, getTodaysMeals, getTodaysWorkouts } from "../api/equo"

const USER_ID = 1 // hardcoded for now

export default function Dashboard() {
    const [summary, setSummary] = useState(null)
    const [meals, setMeals] = useState([])
    const [workouts, setWorkouts] = useState([])
    const [isMetric, setIsMetric] = useState(false)
    
    // Fetches data once in the component when the page loads
    useEffect(() => {
        getToday(USER_ID).then(setSummary)
        getTodaysMeals(USER_ID)
            .then(data => setMeals(Array.isArray(data) ? data : [])) // ensure array
            .catch(() => setMeals([]))
        getTodaysWorkouts(USER_ID)
        .then(data => setWorkouts(Array.isArray(data) ? data : []))
        .catch(() => setWorkouts([]))
    }, [])

    if (!summary) return <div className="p-8 text-gray-500">Loading...</div>

    const toDisplayForecast = (kg) => {
        if (isMetric) return `${kg > 0 ? "+" : ""}${kg} kg`
        const lbs = (kg * 2.205).toFixed(2)
        return `${kg > 0 ? "+" : ""}${lbs} lbs`
    }

    const caloriePercent = Math.min((summary.calories_eaten / summary.calorie_target) * 100, 100)
    
    const proteinTarget = Math.round((summary.calorie_target * 0.30) / 4)
    const carbTarget = Math.round((summary.calorie_target * 0.40) / 4)
    const fatTarget = Math.round((summary.calorie_target * 0.30) / 9)

    return (
        <div className="max-w-lg mx-auto p-6 space-y-6">

            {/* header */}
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">Equo</h1>
                <span className="text-gray-500 text-sm">
                    {new Date().toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric"})}
                </span>
                <button
                    onClick={() => setIsMetric(!isMetric)}
                    className="text-xs bg-gray-100 px-3 py-1 rounded-full font-medium text-gray-600"
                >
                    {isMetric ? "kg" : "lbs"}
                </button>
            </div>

            {/* calorie summary */}
            <div className="bg-white rounded-xl shadow p-5 space-y-3">
                <div className="flex justify-between">
                    <span className="font-semibold">Calories Remaining</span>
                    <span className="text-2xl font-bold">{summary.calories_remaining}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                    <div 
                        className="bg-green-500 h-3 rounded-full transition-all"
                        style={{ width: `${caloriePercent}%`}}
                    ></div>
                </div>
                <div className="flex justify-between text-sm text-gray-500">
                    <span>{summary.calories_eaten} eaten</span>
                    <span>{summary.calorie_target} target</span>
                </div>
                <p className="text-sm text-blue-600">{summary.goal_status}</p>
            </div>

            {/* macros */}
            <div className="bg-white rounded-xl shadow p-5 space-y-3">
                <h2 className="font-semibold">Macros</h2>
                {[
                    { label: "Protein", eaten: summary.protein_eaten, target: proteinTarget, color: "bg-blue-500" },
                    { label: "Carbs", eaten: summary.carbs_eaten, target: carbTarget, color: "bg-yellow-400" },
                    { label: "Fat", eaten: summary.fat_eaten, target: fatTarget, color: "bg-red-400"},
                ].map(({ label, eaten, target, color }) => (
                    <div key={label} className="space-y-1">
                        <div className="flex justify-between text-sm">
                            <span>{label}</span>
                            <span>{eaten}g / {target}g</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                            <div
                                className={`${color} h-2 rounded-full`}
                                style={{ width: `${Math.min((eaten / target) * 100, 100)}%`}}
                            />
                        </div>
                    </div>
                ))}
            </div>

            {/* stats */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-xl shadow p-4 text-center">
                    <p className="text-gray-500 text-sm">Burned Today</p>
                    <p className="text-xl font-bold">{summary.calories_burned}</p>
                    <p className="text-gray-400 text-xs">cal</p>
                </div>
                <div className="bg-white rounded-xl shadow p-4 text-center">
                    <p className="text-gray-500 text-sm">Weekly Forecast</p>
                    <p className="text-xl font-bold">
                        {toDisplayForecast(summary.weekly_forecast_kg)}
                    </p>
                </div>
            </div>

            {/* meals */}
            <div className="bg-white rounded-xl shadow p-5">
                <h2 className="font-semibold mb-3">Today's Meals</h2>
                {meals.length === 0
                    ? <p className="text-gray-400 text-sm">No meals logged yet</p>
                    : meals.map(meal => (
                        <div key={meal.id} className="flex justify-between py-2 border-b last:border-0">
                            <div>
                                <p className="text-sm font-medium capitalize">{meal.meal_type}</p>
                                <p className="text-xs text-gray-500">{meal.description}</p>
                            </div>
                            <span className="text-sm font-semibold">{meal.calories} cal</span>
                        </div>
                    ))
                }
            </div>

            {/* workouts */}
            <div className="bg-white rounded-xl shadow p-5">
                <h2 className="font-semibold mb-3">Today's Workouts</h2>
                {workouts.length === 0
                    ? <p className="text-gray-400 text-sm">No workouts logged yet</p>
                    : workouts.map(workout => (
                        <div key={workout.id} className="flex justify-between py-2 border-b last:border-0">
                            <div>
                                <p className="text-sm font-medium capitalize">{workout.activity_type}</p>
                                <p className="text-xs text-gray-500">{workout.duration_minutes} min</p>
                            </div>
                            <span className="text-sm font-semibold">{workout.calories_burned} cal</span>
                        </div>
                    ))
                }
            </div>

            {/* nav buttons */}
            <div className="grid grid-cols-2 gap-4">
                <a href="/log-meal" className="bg-green-500 text-white text-center py-3 rounded-xl font-semibold">
                    Log Meal
                </a>
                <a href="log-workout" className="bg-blue-500 text-white text-center py-3 rounded-xl font-semibold">
                    Log Workout
                </a>
            </div>

        </div>
    )
}