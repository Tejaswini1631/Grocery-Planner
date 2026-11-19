const express = require("express");
const cors = require("cors");
require("dotenv").config();

const app = express();

// Import routes
const householdRoutes = require("./routes/householdRoutes");
const pantryRoutes = require("./routes/pantryRoutes");
const shoppingRoutes = require("./routes/shoppingRoutes");
const preferencesRoutes = require("./routes/preferencesRoutes");
// Middleware
app.use(cors());
app.use(express.json());
app.use("/api/households", householdRoutes);
app.use("/api/pantry", pantryRoutes);
app.use("/api/shopping", shoppingRoutes);
app.use("/api/preferences", preferencesRoutes);
// Home route
app.get("/", (req, res) => {
    res.json({
        message: "Welcome to Meal & Grocery Planner API",
        status: "Server Running Successfully"
    });
});

// Household routes


// Start server
const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});