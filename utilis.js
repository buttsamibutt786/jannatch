// Modern JavaScript Utility Toolkit

const toolkit = {
    // 1. Math Utility: Calculate percentage
    calculatePercentage: (value, total) => {
        return `${((value / total) * 100).toFixed(2)}%`;
    },

    // 2. String Utility: Capitalize first letter
    capitalize: (str) => {
        if (!str) return "";
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    // 3. Array Utility: Remove duplicates
    removeDuplicates: (arr) => {
        return [...new Set(arr)];
    },

    // 4. Date Utility: Get current timestamp
    getTimestamp: () => {
        return new Date().toLocaleString();
    }
};

// Example Usage:
console.log("--- My Utility Toolkit ---");
console.log("Percentage:", toolkit.calculatePercentage(75, 100));
console.log("Capitalized:", toolkit.capitalize("hello lenovo user"));
console.log("Unique Array:", toolkit.removeDuplicates([1, 2, 2, 3, 4, 4, 5]));
console.log("Current Time:", toolkit.getTimestamp());

export default toolkit;