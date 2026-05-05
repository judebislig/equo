// src/pages/LogMeal.jsx
import { useState } from "react"
import { parseMeal, logMeal } from "../api/equo"

const USER_ID = 1
const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]

export default function LogMeal() {
    const [description, setDescription] = useState("")
    const [mealType, setMealType] = useState("lunch")
    const [preview, setPreview] = useState(null)
    const [loading, setLoading] = useState(false)
    const [logged, setLogged] = useState(false)
    const [logging, setLogging] = useState(false)

    const handleParse = async() => {
        if (loading) return
        setLoading(true)
        const result = await parseMeal(description)
        setPreview(result)
        setLoading(false)
    }

    const handleLog = async () => {
        if (logging) return
        setLogging(true)
        await logMeal(USER_ID, mealType, description)
        setLogging(false)
        setLogged(true)
    }

    if (logged) return (
        <div className="max-w-lg mx-auto p-6 text-center space-y-4">
            <p className="text-2xl">✓</p>
            <p className="font-semibold">Meal logged</p>
            <a href="/" className="text-blue-500 text-sm">Back to dashboard</a>
        </div>
    )

    return (
        <div className="max-w-lg mx-auto p-6 space-y-6">
            <div className="flex items-center gap-3">
                <a href="/" className="text-gray-400">←</a>
                <h1 className="text-xl font-bold">Log a Meal</h1>
            </div>

            {/* description input */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">What did you eat?</label>
                <textarea
                    className="w-full border rounded-xl p-3 text-sm resize-none focus:outline-none focus:ring-green-400"
                    rows={3}
                    placeholder="chicken rice and broccoli..."
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                />
            </div>

            {/* meal type */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Meal type</label>
                <div className="grid grid-cols-4 gap-2">
                    {MEAL_TYPES.map(type => (
                        <button
                            key={type}
                            onClick={() => setMealType(type)}
                            className={`py rounded-lg text-sm capitalize ${
                                mealType === type
                                    ? "bg-green-500 text-white"
                                    : "bg-gray-100 text-gray-600"
                            }`}
                        >
                            {type}
                        </button>
                    ))}
                </div>
            </div>

            {/* parse button */}
            <button
                onClick={handleParse}
                disabled={!description || loading}
                className="w-full bg-gray-800 text-white py-3 rounded-xl font-semibold disabled:opacity-40"
            >
                {loading ? "Parsing..." : "Parse & Preview"}
            </button>

            {/* preview */}
            {preview && (
                <div className="bg-gray-50 rounded-xl p-4 space-y-2">
                    <p className="font-medium text-sm">{preview.food_name}</p>
                    <div className="grid grid-cols-4 gap-2 text-center">
                        {[
                            { label: "Cal", value: preview.calories },
                            { label: "Protein", value: `${preview.protein}g` },
                            { label: "Carbs", value: `${preview.carbs}g` },
                            { label: "Fat", value: `${preview.fat}g` },
                        ].map(({ label, value }) => (
                            <div key={label} className="bg-white rounded-lg p-2">
                                <p className="text-xs text-gray-500">{label}</p>
                                <p className="font-semibold text-sm">{value}</p>
                            </div>
                        ))}
                    </div>
                    {preview.is_estimated && (
                        <p className="text-xs text-amber-500">⚠ Some values estimated</p>
                    )}
                    <button
                        onClick={handleLog}
                        disabled={logging}
                        className="w-full bg-green-500 text-white py-3 rounded-xl font-semibold disabled:opacity-40 mt-2"
                    >
                        {logging ? "Logging..." : "Log Meal"}
                    </button>
                </div>
            )}
        </div>
    )
}