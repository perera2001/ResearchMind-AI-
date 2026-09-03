const axios = require("axios");


const pythonApi = axios.create({
    baseURL: process.env.PYTHON_AI_SERVICE_URL,
    timeout: 120000,
});


module.exports = pythonApi;
