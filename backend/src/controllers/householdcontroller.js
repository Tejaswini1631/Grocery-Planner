// Create a household
const createHousehold = (req, res) => {
    const { household_name, address } = req.body;

    if (!household_name) {
        return res.status(400).json({
            message: "Household name is required"
        });
    }

    res.status(201).json({
        message: "Household created successfully",
        household: {
            household_name,
            address
        }
    });
};

// Get household details
const getHousehold = (req, res) => {
    const { id } = req.params;

    res.status(200).json({
        message: "Household details fetched successfully",
        household_id: id
    });
};

module.exports = {
    createHousehold,
    getHousehold
};