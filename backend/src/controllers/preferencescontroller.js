
const getPreferences = (req, res) => {
    const { userId } = req.params;

    res.status(200).json({
        message: "Preferences fetched successfully",
        user_id: userId,
        preferences: {
            diet_type: "Vegetarian",
            servings: 4
        }
    });
};


const updatePreferences = (req, res) => {
    const { userId } = req.params;
    const { diet_type, servings } = req.body;

    res.status(200).json({
        message: "Preferences updated successfully",
        user_id: userId,
        preferences: {
            diet_type,
            servings
        }
    });
};

module.exports = {
    getPreferences,
    updatePreferences
};