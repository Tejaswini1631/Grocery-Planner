const express = require("express");
const router = express.Router();

const {
    addPantryItem,
    getPantryItems,
    updatePantryItem,
    deletePantryItem
} = require("../controllers/pantryController");

router.post("/", addPantryItem);
router.get("/", getPantryItems);
router.put("/:id", updatePantryItem);
router.delete("/:id", deletePantryItem);

module.exports = router;