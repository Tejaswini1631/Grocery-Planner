const express = require("express");
const router = express.Router();

const {
    addShoppingItem,
    getShoppingList,
    updateShoppingItem,
    deleteShoppingItem
} = require("../controllers/shoppingController");

router.post("/", addShoppingItem);
router.get("/", getShoppingList);
router.put("/:id", updateShoppingItem);
router.delete("/:id", deleteShoppingItem);

module.exports = router;