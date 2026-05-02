// src/api/equo.js
const BASE_URL = "http://18.224.179.88:8000" // EC2 instance

export const getToday = async (userId) => {
    const res = await fetch(`${BASE_URL}/summary/${userId}/today`)
    return res.json()
}

export const parseMeal = async (description) => {
    const res = await fetch(`${BASE_URL}/meals/parse?description=${encodeURIComponent(description)}`)
    return res.json()
}

export const logMeal = async (userId, mealType, description) => {
    const res = await fetch(`${BASE_URL}/meals/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, meal_type: mealType, description})
    })
    return res.json()
}

export const logWorkout = async (userId, activityType, durationMinutes, caloriesOverride, notes) => {
    const res = await fetch(`${BASE_URL}/workouts/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: userId,
            activity_type: activityType,
            duration_minutes: durationMinutes,
            calories_override: caloriesOverride || null,
            notes: notes || null
        })
    })
    return res.json()
}

export const getTodaysMeals = async (userId) => {
    const res = await fetch(`${BASE_URL}/meals/${userId}/today`)
    return res.json()
}

export const getTodaysWorkouts = async (userId) => {
    const res = await fetch(`${BASE_URL}/workouts/${userId}/today`)
    return res.json()
}