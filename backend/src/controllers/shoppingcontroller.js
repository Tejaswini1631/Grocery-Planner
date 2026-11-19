
const addShoppingItem = (req, res) => {
    const { household_id, item_name, quantity, unit } = req.body;

    if (!household_id || !item_name || !quantity || !unit) {
        return res.status(400).json({
            message: "Please provide all shopping item details"
        });
    }

    res.status(201).json({
        message: "Shopping item added successfully",
        shopping_item: {
            household_id,
            item_name,
            quantity,
            unit
        }
    });
};

const getShoppingList = (req, res) => {
    const { household_id } = req.query;

    res.status(200).json({
        message: "Shopping list fetched successfully",
        household_id,
        items: []
    });
};


const updateShoppingItem = (req, res) => {
    const { id } = req.params;
    const { item_name, quantity, unit } = req.body;

    res.status(200).json({
        message: "Shopping item updated successfully",
        shopping_item: {
            id,
            item_name,
            quantity,
            unit
        }
    });
};


const deleteShoppingItem = (req, res) => {
    const { id } = req.params;

    res.status(200).json({
        message: "Shopping item deleted successfully",
        shopping_item_id: id
    });
};

module.exports = {
    addShoppingItem,
    getShoppingList,
    updateShoppingItem,
    deleteShoppingItem
};