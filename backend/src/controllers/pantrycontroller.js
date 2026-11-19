
const addPantryItem = (req, res) => {
    const {
        household_id,
        ingredient_id,
        quantity,
        unit,
        expiry_date
    } = req.body;

    if (!household_id || !ingredient_id || !quantity || !unit) {
        return res.status(400).json({
            message: "Please provide all required pantry details"
        });
    }

    res.status(201).json({
        message: "Pantry item added successfully",
        pantry_item: {
            household_id,
            ingredient_id,
            quantity,
            unit,
            expiry_date
        }
    });
};


const getPantryItems = (req, res) => {
    const { household_id } = req.query;

    res.status(200).json({
        message: "Pantry items fetched successfully",
        household_id,
        items: []
    });
};

const updatePantryItem = (req, res) => {
    const { id } = req.params;
    const { quantity, unit, expiry_date } = req.body;

    res.status(200).json({
        message: "Pantry item updated successfully",
        pantry_item: {
            id,
            quantity,
            unit,
            expiry_date
        }
    });
};


const deletePantryItem = (req, res) => {
    const { id } = req.params;

    res.status(200).json({
        message: "Pantry item deleted successfully",
        pantry_item_id: id
    });
};
module.exports = {
    addPantryItem,
    getPantryItems,
    updatePantryItem,
    deletePantryItem
};