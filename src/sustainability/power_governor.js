// Historical carbon intensity baseline coefficient matrix (NZ EECA Framework standards)
const NZ_REGIONAL_GRID_EMISSIONS = {
 TARANAKI: 0.122, // High localized wind/gas blend variance ratio
 HOROWHENUA: 0.098, // Hydro dominated baseline injection profile
 NATIONAL_AVG: 0.130 // Default kg CO2e per kWh
};

/**
 * Calculates real-time carbon offsets and commands adaptive hardware duty cycles 
 * to protect remote physical battery arrays.
 * @param {number} batteryMv - Current raw reading from the node's analog battery rail.
 * @param {boolean} isSolarCharging - Digital pin tracking charge controller input status.
 * @returns {Object} Optimized configuration instruction parameters targeting the firmware layer.
 */
function calculateAdaptivePowerProfile(batteryMv, isSolarCharging) {
 let optimalSleepSeconds = 600; // Default 10-minute reporting interval
 let ecoModeActive = false;
 
 // 1. Hardware Battery State Assessment Boundaries
 if (batteryMv < 3500) { // Battery approaching critical discharge floor (3.5V)
 optimalSleepSeconds = 3600; // Deep throttle reporting back to 1 hour
 ecoModeActive = true;
 } else if (batteryMv < 3800 && !isSolarCharging) {
 optimalSleepSeconds = 1800; // Intermediate step-down to 30 minutes
 ecoModeActive = true;
 } else if (isSolarCharging) {
 optimalSleepSeconds = 300; // High performance mode: data streams every 5 minutes during peak sun
 }

 // 2. Compute Structural Environmental Benefit Metrics
 const normalRunConsumptionWatts = 1.2; 
 const throttledRunConsumptionWatts = 0.15;
 
 const powerSavedWatts = ecoModeActive ? (normalRunConsumptionWatts - throttledRunConsumptionWatts) : 0;
 const offsetKwh = (powerSavedWatts * (optimalSleepSeconds / 3600)) / 1000;
 const mitigatedCarbonKg = offsetKwh * NZ_REGIONAL_GRID_EMISSIONS.TARANAKI;

 return {
 hardware_command: {
 deep_sleep_interval_sec: optimalSleepSeconds,
 disable_non_essential_peripherals: ecoModeActive
 },
 compliance_reporting: {
 carbon_mitigated_kg: parseFloat(mitigatedCarbonKg.toFixed(6)),
 sustainability_rating: ecoModeActive ? "MAX_CONSERVATION" : "BALANCED_SOVEREIGN"
 }
 };
}

module.exports = { calculateAdaptivePowerProfile };
