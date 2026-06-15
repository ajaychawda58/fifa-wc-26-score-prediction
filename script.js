// --- Global State ---
let modelParameters = null;
let worldCupMatches = [];
let squadRosters = {};
let selectedModel = "ensemble"; // Default active model

const GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Türkiye"],
    "E": ["Ivory Coast", "Curaçao", "Ecuador", "Germany"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Iraq", "Norway", "Senegal"],
    "J": ["Algeria", "Argentina", "Austria", "Jordan"],
    "K": ["Colombia", "DR Congo", "Portugal", "Uzbekistan"],
    "L": ["Croatia", "England", "Ghana", "Panama"]
};

// Default formations coordinates on the pitch (percentages from top-left)
const FORMATIONS = {
    "4-3-3": [
        { role: "GK", x: 50, y: 88, name: "GK" },
        { role: "LB", x: 15, y: 68, name: "LB" },
        { role: "CB", x: 38, y: 72, name: "LCB" },
        { role: "CB", x: 62, y: 72, name: "RCB" },
        { role: "RB", x: 85, y: 68, name: "RB" },
        { role: "CM", x: 30, y: 48, name: "LCM" },
        { role: "DM", x: 50, y: 54, name: "DM" },
        { role: "CM", x: 70, y: 48, name: "RCM" },
        { role: "LW", x: 20, y: 22, name: "LW" },
        { role: "CF", x: 50, y: 18, name: "CF" },
        { role: "RW", x: 80, y: 22, name: "RW" }
    ],
    "4-2-3-1": [
        { role: "GK", x: 50, y: 88, name: "GK" },
        { role: "LB", x: 15, y: 68, name: "LB" },
        { role: "CB", x: 38, y: 72, name: "LCB" },
        { role: "CB", x: 62, y: 72, name: "RCB" },
        { role: "RB", x: 85, y: 68, name: "RB" },
        { role: "DM", x: 35, y: 55, name: "LDM" },
        { role: "DM", x: 65, y: 55, name: "RDM" },
        { role: "AM", x: 20, y: 35, name: "RAM" },
        { role: "AM", x: 50, y: 32, name: "AM" },
        { role: "AM", x: 80, y: 35, name: "LAM" },
        { role: "CF", x: 50, y: 16, name: "CF" }
    ],
    "3-4-3": [
        { role: "GK", x: 50, y: 88, name: "GK" },
        { role: "CB", x: 28, y: 72, name: "LCB" },
        { role: "CB", x: 50, y: 74, name: "CB" },
        { role: "CB", x: 72, y: 72, name: "RCB" },
        { role: "LM", x: 15, y: 50, name: "LWB" },
        { role: "CM", x: 38, y: 52, name: "LCM" },
        { role: "CM", x: 62, y: 52, name: "RCM" },
        { role: "RM", x: 85, y: 50, name: "RWB" },
        { role: "LW", x: 25, y: 22, name: "LW" },
        { role: "CF", x: 50, y: 18, name: "CF" },
        { role: "RW", x: 75, y: 22, name: "RW" }
    ],
    "3-4-2-1": [
        { role: "GK", x: 50, y: 88, name: "GK" },
        { role: "CB", x: 28, y: 72, name: "LCB" },
        { role: "CB", x: 50, y: 74, name: "CB" },
        { role: "CB", x: 72, y: 72, name: "RCB" },
        { role: "LM", x: 15, y: 50, name: "LWB" },
        { role: "CM", x: 38, y: 52, name: "LCM" },
        { role: "CM", x: 62, y: 52, name: "RCM" },
        { role: "RM", x: 85, y: 50, name: "RWB" },
        { role: "AM", x: 32, y: 32, name: "LAM" },
        { role: "AM", x: 68, y: 32, name: "RAM" },
        { role: "CF", x: 50, y: 16, name: "CF" }
    ],
    "3-4-1-2": [
        { role: "GK", x: 50, y: 88, name: "GK" },
        { role: "CB", x: 28, y: 72, name: "LCB" },
        { role: "CB", x: 50, y: 74, name: "CB" },
        { role: "CB", x: 72, y: 72, name: "RCB" },
        { role: "LM", x: 15, y: 50, name: "LWB" },
        { role: "CM", x: 38, y: 52, name: "LCM" },
        { role: "CM", x: 62, y: 52, name: "RCM" },
        { role: "RM", x: 85, y: 50, name: "RWB" },
        { role: "AM", x: 50, y: 32, name: "AM" },
        { role: "CF", x: 35, y: 18, name: "LCF" },
        { role: "CF", x: 65, y: 18, name: "RCF" }
    ],
    "3-5-2": [
        { role: "GK", x: 50, y: 88, name: "GK" },
        { role: "CB", x: 28, y: 72, name: "LCB" },
        { role: "CB", x: 50, y: 74, name: "CB" },
        { role: "CB", x: 72, y: 72, name: "RCB" },
        { role: "LM", x: 15, y: 48, name: "LM" },
        { role: "DM", x: 50, y: 56, name: "DM" },
        { role: "CM", x: 35, y: 44, name: "LCM" },
        { role: "CM", x: 65, y: 44, name: "RCM" },
        { role: "RM", x: 85, y: 48, name: "RM" },
        { role: "CF", x: 35, y: 18, name: "LCF" },
        { role: "CF", x: 65, y: 18, name: "RCF" }
    ]
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", async () => {
    setupTabNavigation();
    await loadApplicationData();
    setupModelSelector();
    populateDropdowns();
    renderFixturesTable();
    initDashboardWidgets();
});

// --- Tab System Navigation ---
function setupTabNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(t => t.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
            
            if (targetTab === "standings-tab") {
                renderGroupStandings();
            } else if (targetTab === "squads-tab") {
                renderSquadTab();
            }
        });
    });
}

// --- Data Fetching & Parsers ---
async function loadApplicationData() {
    try {
        console.log("Fetching model parameters and schedule JSON...");
        const cacheBuster = `?v=${Date.now()}`;
        
        const [paramsRes, matchesRes, mdRes] = await Promise.all([
            fetch(`data/model_parameters.json${cacheBuster}`),
            fetch(`data/wc_2026_matches.json${cacheBuster}`),
            fetch(`data/player_profiles.md${cacheBuster}`)
        ]);
        
        modelParameters = await paramsRes.json();
        worldCupMatches = await matchesRes.json();
        
        // Sort matches chronologically by date
        worldCupMatches.sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id);
        
        const mdText = await mdRes.text();
        squadRosters = parseSquadsMarkdown(mdText);
        
        console.log("All data loaded successfully!");
        updateHeaderStats();
    } catch (e) {
        console.error("Failed to load application data: ", e);
    }
}

function parseSquadsMarkdown(mdText) {
    const teams = mdText.split(/##\s+/);
    const squads = {};
    for (let teamSection of teams) {
        if (!teamSection.trim() || teamSection.startsWith('#')) continue;
        const lines = teamSection.split('\n');
        const header = lines[0].replace('Squad Profile', '').trim();
        squads[header] = [];
        
        let inTable = false;
        for (let line of lines) {
            if (line.includes('| No. | Position |')) {
                inTable = true;
                continue;
            }
            if (inTable && line.startsWith('|')) {
                if (line.includes('---')) continue;
                const cols = line.split('|').map(c => c.trim()).filter(Boolean);
                if (cols.length >= 7) {
                    squads[header].push({
                        no: cols[0],
                        pos: cols[1],
                        name: cols[2],
                        age: cols[3],
                        caps: cols[4],
                        goals: cols[5],
                        club: cols[6]
                    });
                }
            }
        }
    }
    return squads;
}

// Helper to pull prediction record based on currently selected model
function getPredictionRecord(match, modelName) {
    if (match.predictions && match.predictions[modelName]) {
        return match.predictions[modelName];
    }
    // Fallback to top-level legacy fields if nested fields are missing
    return match;
}

function updateHeaderStats() {
    let completedCount = 0;
    let correctOutcomeCount = 0;
    
    worldCupMatches.forEach(m => {
        if (m.home_score !== null && m.away_score !== null) {
            completedCount++;
            
            const actualHome = parseInt(m.home_score);
            const actualAway = parseInt(m.away_score);
            
            const pred = getPredictionRecord(m, selectedModel);
            const predHome = parseInt(pred.predicted_home_score);
            const predAway = parseInt(pred.predicted_away_score);
            
            const actualOutcome = actualHome > actualAway ? "H" : actualAway > actualHome ? "A" : "D";
            const predOutcome = predHome > predAway ? "H" : predAway > predHome ? "A" : "D";
            
            if (actualOutcome === predOutcome) {
                correctOutcomeCount++;
            }
        }
    });
    
    const accuracy = completedCount > 0 ? ((correctOutcomeCount / completedCount) * 100).toFixed(1) + "%" : "0%";
    
    document.getElementById("model-accuracy").innerText = accuracy;
    document.getElementById("played-count").innerText = `${completedCount} / 72`;
    document.getElementById("total-predicted").innerText = worldCupMatches.length;
}

// --- Model Selector Hook ---
function setupModelSelector() {
    const selector = document.getElementById("model-select");
    if (!selector) return;
    
    selector.addEventListener("change", (e) => {
        selectedModel = e.target.value;
        console.log(`Switched active model to: ${selectedModel}`);
        
        // Refresh UI components
        updateHeaderStats();
        renderFixturesTable();
        
        // Update comparison / prediction panel if prediction already run
        const teamA = document.getElementById("team-a-select").value;
        const teamB = document.getElementById("team-b-select").value;
        if (document.getElementById("prediction-results").style.display !== "none") {
            runVisualPrediction(teamA, teamB);
        }
        
        // Refresh standings simulation if standings tab is active
        const standingsTab = document.getElementById("standings-tab");
        if (standingsTab.classList.contains("active")) {
            renderGroupStandings();
        }
    });
}

function populateDropdowns() {
    if (!modelParameters) return;
    
    const teamASelect = document.getElementById("team-a-select");
    const teamBSelect = document.getElementById("team-b-select");
    const squadSelect = document.getElementById("squad-team-select");
    
    const sortedTeams = Object.keys(modelParameters.dixon_coles.teams).sort();
    
    const generateOptions = (selectEl, defaultTeam) => {
        selectEl.innerHTML = "";
        sortedTeams.forEach(team => {
            const opt = document.createElement("option");
            opt.value = team;
            opt.innerText = team;
            if (team === defaultTeam) opt.selected = true;
            selectEl.appendChild(opt);
        });
    };
    
    generateOptions(teamASelect, "Argentina");
    generateOptions(teamBSelect, "France");
    generateOptions(squadSelect, "Argentina");
}

// --- Predictor Logic ---
function initDashboardWidgets() {
    const btnPredict = document.getElementById("btn-predict");
    
    btnPredict.addEventListener("click", () => {
        const teamA = document.getElementById("team-a-select").value;
        const teamB = document.getElementById("team-b-select").value;
        
        if (teamA === teamB) {
            alert("Please select two different teams!");
            return;
        }
        
        runVisualPrediction(teamA, teamB);
    });
}

// Mathematical Helper Functions
const factorial = (n) => (n <= 1 ? 1 : n * factorial(n - 1));
const poissonPmf = (k, lambda) => Math.exp(-lambda) * Math.pow(lambda, k) / factorial(k);

function getDixonColesTau(x, y, lambda, mu, rho) {
    if (x === 0 && y === 0) return 1.0 - rho * lambda * mu;
    if (x === 1 && y === 0) return 1.0 + rho * mu;
    if (x === 0 && y === 1) return 1.0 + rho * lambda;
    if (x === 1 && y === 1) return 1.0 - rho;
    return 1.0;
}

function bivariatePoissonPmf(x, y, l1, l2, l3) {
    let ans = 0.0;
    const minXY = Math.min(x, y);
    for (let k = 0; k <= minXY; k++) {
        let term = Math.pow(l1, x - k) * Math.pow(l2, y - k) * Math.pow(l3, k) / 
                   (factorial(x - k) * factorial(y - k) * factorial(k));
        ans += term;
    }
    return ans * Math.exp(-(l1 + l2 + l3));
}

// --- Client-Side Model Predictors ---

// 1. Dixon-Coles Predictor
function predictDixonColes(teamA, teamB, maxGoals=5) {
    const dc = modelParameters.dixon_coles;
    const ratingsA = dc.teams[teamA];
    const ratingsB = dc.teams[teamB];
    const isHomeA = ["USA", "Canada", "Mexico"].includes(teamA);
    const haMult = isHomeA ? dc.home_advantage_multiplier : 1.0;
    
    const lambda = ratingsA.attack * ratingsB.defense * haMult;
    const mu = ratingsB.attack * ratingsA.defense;
    const rho = dc.rho;
    
    const grid = [];
    let sum = 0;
    for (let x = 0; x <= maxGoals; x++) {
        grid[x] = [];
        for (let y = 0; y <= maxGoals; y++) {
            let prob = poissonPmf(x, lambda) * poissonPmf(y, mu);
            prob *= getDixonColesTau(x, y, lambda, mu, rho);
            grid[x][y] = prob;
            sum += prob;
        }
    }
    
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            grid[x][y] /= sum;
        }
    }
    
    return buildOutcomeRecord(grid, lambda, mu);
}

// 2. Bivariate Poisson Predictor
function predictBivariate(teamA, teamB, maxGoals=5) {
    const bp = modelParameters.bivariate;
    const ratingsA = bp.teams[teamA];
    const ratingsB = bp.teams[teamB];
    const isHomeA = ["USA", "Canada", "Mexico"].includes(teamA);
    const haMult = isHomeA ? bp.home_advantage_multiplier : 1.0;
    
    const l1 = ratingsA.attack * ratingsB.defense * haMult;
    const l2 = ratingsB.attack * ratingsA.defense;
    const l3 = Math.exp(bp.log_covariance);
    
    const grid = [];
    let sum = 0;
    for (let x = 0; x <= maxGoals; x++) {
        grid[x] = [];
        for (let y = 0; y <= maxGoals; y++) {
            let prob = bivariatePoissonPmf(x, y, l1, l2, l3);
            grid[x][y] = prob;
            sum += prob;
        }
    }
    
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            grid[x][y] /= sum;
        }
    }
    
    return buildOutcomeRecord(grid, l1 + l3, l2 + l3);
}

// 3. Elo-Poisson Predictor
function predictEloPoisson(teamA, teamB, maxGoals=5) {
    const elo = modelParameters.elo;
    const ratingA = elo.teams[teamA].rating;
    const ratingB = elo.teams[teamB].rating;
    const eloDiff = ratingA - ratingB;
    const isHomeA = ["USA", "Canada", "Mexico"].includes(teamA) ? 1.0 : 0.0;
    
    const lambda = Math.exp(elo.beta_0 + elo.beta_1 * eloDiff + elo.beta_ha * isHomeA);
    const mu = Math.exp(elo.beta_0 - elo.beta_1 * eloDiff);
    
    const grid = [];
    let sum = 0;
    for (let x = 0; x <= maxGoals; x++) {
        grid[x] = [];
        for (let y = 0; y <= maxGoals; y++) {
            let prob = poissonPmf(x, lambda) * poissonPmf(y, mu);
            grid[x][y] = prob;
            sum += prob;
        }
    }
    
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            grid[x][y] /= sum;
        }
    }
    
    return buildOutcomeRecord(grid, lambda, mu);
}

// 4. Softmax Classifier Predictor
function predictSoftmaxClassifier(teamA, teamB, maxGoals=5) {
    const cl = modelParameters.classifier;
    const elo = modelParameters.elo;
    const dc = modelParameters.dixon_coles;
    
    const ratingA = elo.teams[teamA].rating;
    const ratingB = elo.teams[teamB].rating;
    const eloDiff = ratingA - ratingB;
    
    const rankA = dc.teams[teamA].rank;
    const rankB = dc.teams[teamB].rank;
    const rankDiff = rankB - rankA;
    
    const isHomeA = ["USA", "Canada", "Mexico"].includes(teamA) ? 1.0 : 0.0;
    
    const xVec = [1.0, eloDiff, rankDiff, isHomeA];
    let zh = 0, zd = 0;
    for (let i = 0; i < 4; i++) {
        zh += xVec[i] * cl.w_home[i];
        zd += xVec[i] * cl.w_draw[i];
    }
    
    const expH = Math.exp(zh);
    const expD = Math.exp(zd);
    const denom = expH + expD + 1.0;
    
    const pH = expH / denom;
    const pD = expD / denom;
    const pA = 1.0 / denom;
    
    // xG projections borrowed from Elo expected goals
    const l1 = Math.exp(elo.beta_0 + elo.beta_1 * eloDiff + elo.beta_ha * isHomeA);
    const l2 = Math.exp(elo.beta_0 - elo.beta_1 * eloDiff);
    
    // Build Poisson grid and scale parts to match pH, pD, pA
    const grid = [];
    let sumW = 0, sumD = 0, sumL = 0;
    for (let x = 0; x <= maxGoals; x++) {
        grid[x] = [];
        for (let y = 0; y <= maxGoals; y++) {
            let p = poissonPmf(x, l1) * poissonPmf(y, l2);
            grid[x][y] = p;
            if (x > y) sumW += p;
            else if (x === y) sumD += p;
            else sumL += p;
        }
    }
    
    // Re-scale grid components
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            if (x > y && sumW > 0) grid[x][y] *= (pH / sumW);
            else if (x === y && sumD > 0) grid[x][y] *= (pD / sumD);
            else if (y > x && sumL > 0) grid[x][y] *= (pA / sumL);
        }
    }
    
    let gridSum = 0;
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            gridSum += grid[x][y];
        }
    }
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            grid[x][y] /= gridSum;
        }
    }
    
    return {
        home_xG: l1,
        away_xG: l2,
        home_win: pH,
        away_win: pA,
        draw: pD,
        score_probabilities: grid
    };
}

// 5. Ensemble Predictor
function predictEnsemble(teamA, teamB, maxGoals=5) {
    const dc = predictDixonColes(teamA, teamB, maxGoals);
    const bp = predictBivariate(teamA, teamB, maxGoals);
    const elo = predictEloPoisson(teamA, teamB, maxGoals);
    const cl = predictSoftmaxClassifier(teamA, teamB, maxGoals);
    
    const w_dc = 0.35, w_bp = 0.20, w_elo = 0.30, w_cl = 0.15;
    
    const home_xG = w_dc * dc.home_xG + w_bp * bp.home_xG + w_elo * elo.home_xG + w_cl * cl.home_xG;
    const away_xG = w_dc * dc.away_xG + w_bp * bp.away_xG + w_elo * elo.away_xG + w_cl * cl.away_xG;
    
    const home_win = w_dc * dc.home_win + w_bp * bp.home_win + w_elo * elo.home_win + w_cl * cl.home_win;
    const away_win = w_dc * dc.away_win + w_bp * bp.away_win + w_elo * elo.away_win + w_cl * cl.away_win;
    const draw = w_dc * dc.draw + w_bp * bp.draw + w_elo * elo.draw + w_cl * cl.draw;
    
    const grid = [];
    for (let x = 0; x <= maxGoals; x++) {
        grid[x] = [];
        for (let y = 0; y <= maxGoals; y++) {
            grid[x][y] = w_dc * dc.score_probabilities[x][y] + 
                         w_bp * bp.score_probabilities[x][y] + 
                         w_elo * elo.score_probabilities[x][y] + 
                         w_cl * cl.score_probabilities[x][y];
        }
    }
    
    return {
        home_xG: home_xG,
        away_xG: away_xG,
        home_win: home_win,
        away_win: away_win,
        draw: draw,
        score_probabilities: grid
    };
}

// Utility to build probabilities from grid
function buildOutcomeRecord(grid, lambda, mu) {
    let winA = 0, winB = 0, draw = 0;
    const maxGoals = grid.length - 1;
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            if (x > y) winA += grid[x][y];
            else if (y > x) winB += grid[x][y];
            else draw += grid[x][y];
        }
    }
    return {
        home_xG: lambda,
        away_xG: mu,
        home_win: winA,
        away_win: winB,
        draw: draw,
        score_probabilities: grid
    };
}

function runVisualPrediction(teamA, teamB) {
    if (!modelParameters) return;
    
    let pred;
    if (selectedModel === "dixon_coles") pred = predictDixonColes(teamA, teamB);
    else if (selectedModel === "bivariate") pred = predictBivariate(teamA, teamB);
    else if (selectedModel === "elo") pred = predictEloPoisson(teamA, teamB);
    else if (selectedModel === "classifier") pred = predictSoftmaxClassifier(teamA, teamB);
    else pred = predictEnsemble(teamA, teamB);
    
    const lambda = pred.home_xG;
    const mu = pred.away_xG;
    const grid = pred.score_probabilities;
    
    // Find most likely score
    let maxProb = 0;
    let scoreHome = 0;
    let scoreAway = 0;
    const maxGoals = grid.length - 1;
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            if (grid[x][y] > maxProb) {
                maxProb = grid[x][y];
                scoreHome = x;
                scoreAway = y;
            }
        }
    }
    
    // --- Update UI ---
    document.getElementById("xg-team-a").innerText = teamA;
    document.getElementById("xg-team-b").innerText = teamB;
    document.getElementById("xg-val-a").innerText = lambda.toFixed(2);
    document.getElementById("xg-val-b").innerText = mu.toFixed(2);
    
    const winAPercent = Math.round(pred.home_win * 100);
    const winBPercent = Math.round(pred.away_win * 100);
    const drawPercent = 100 - winAPercent - winBPercent;
    
    document.getElementById("prob-lbl-a").innerText = `${teamA}: ${winAPercent}%`;
    document.getElementById("prob-lbl-b").innerText = `${teamB}: ${winBPercent}%`;
    document.getElementById("prob-bar-a").style.width = `${winAPercent}%`;
    document.getElementById("prob-bar-b").style.width = `${winBPercent}%`;
    document.getElementById("prob-bar-draw").style.width = `${drawPercent}%`;
    
    document.getElementById("predicted-score-text").innerText = `${scoreHome} - ${scoreAway}`;
    document.getElementById("predicted-score-prob").innerText = `Score probability: ${(maxProb * 100).toFixed(1)}%`;
    document.getElementById("prediction-results").style.display = "block";
    
    renderHeatmap(teamA, teamB, grid);
    
    // Ratings display using Dixon-Coles parameters for base rating display
    const dc = modelParameters.dixon_coles;
    const ratingsA = dc.teams[teamA];
    const ratingsB = dc.teams[teamB];
    
    document.getElementById("comp-team-a-name").innerText = teamA;
    document.getElementById("comp-team-b-name").innerText = teamB;
    document.getElementById("comp-att-a").innerText = ratingsA.attack.toFixed(2);
    document.getElementById("comp-def-a").innerText = ratingsA.defense.toFixed(2);
    document.getElementById("comp-att-b").innerText = ratingsB.attack.toFixed(2);
    document.getElementById("comp-def-b").innerText = ratingsB.defense.toFixed(2);
    
    const getFillPercent = (val) => Math.min(100, Math.max(10, ((val - 0.4) / 1.4) * 100));
    const getDefFillPercent = (val) => Math.min(100, Math.max(10, (1 - (val - 0.4) / 1.4) * 100));
    
    document.getElementById("comp-att-a-bar").style.width = `${getFillPercent(ratingsA.attack)}%`;
    document.getElementById("comp-att-b-bar").style.width = `${getFillPercent(ratingsB.attack)}%`;
    document.getElementById("comp-def-a-bar").style.width = `${getDefFillPercent(ratingsA.defense)}%`;
    document.getElementById("comp-def-b-bar").style.width = `${getDefFillPercent(ratingsB.defense)}%`;
    
    document.getElementById("comp-formation-a").innerText = ratingsA.formation;
    document.getElementById("comp-formation-b").innerText = ratingsB.formation;
    
    renderFormationOnPitch("pitch-team-a", ratingsA.formation);
    renderFormationOnPitch("pitch-team-b", ratingsB.formation);
    
    document.getElementById("comparison-section").style.display = "block";
}

function renderHeatmap(teamA, teamB, grid) {
    const container = document.getElementById("heatmap-placeholder");
    container.innerHTML = "";
    
    const wrapper = document.createElement("div");
    wrapper.className = "heatmap-grid";
    
    const corner = document.createElement("div");
    corner.className = "heatmap-header-cell";
    corner.innerHTML = `<span style="font-size:0.7rem;">${teamA}\\${teamB}</span>`;
    wrapper.appendChild(corner);
    
    for (let y = 0; y <= 5; y++) {
        const cell = document.createElement("div");
        cell.className = "heatmap-header-cell";
        cell.innerText = y;
        wrapper.appendChild(cell);
    }
    
    for (let x = 0; x <= 5; x++) {
        const rowHeader = document.createElement("div");
        rowHeader.className = "heatmap-header-cell";
        rowHeader.innerText = x;
        wrapper.appendChild(rowHeader);
        
        for (let y = 0; y <= 5; y++) {
            const prob = grid[x][y];
            const cell = document.createElement("div");
            cell.className = "heatmap-cell";
            
            const hue = 333;
            const saturation = 90;
            const lightness = 25 + Math.min(50, prob * 200);
            
            cell.style.backgroundColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            if (prob < 0.02) cell.style.color = "rgba(255,255,255,0.4)";
            
            cell.innerHTML = `
                <span>${(prob * 100).toFixed(1)}%</span>
                <span class="heatmap-cell-val">${x}-${y}</span>
            `;
            wrapper.appendChild(cell);
        }
    }
    
    container.appendChild(wrapper);
}

function renderFormationOnPitch(pitchId, formationName) {
    const pitch = document.getElementById(pitchId);
    pitch.innerHTML = "";
    
    const innerCircle = document.createElement("div");
    innerCircle.className = "pitch-center-circle";
    pitch.appendChild(innerCircle);
    
    const topPen = document.createElement("div");
    topPen.className = "pitch-penalty-area-t";
    pitch.appendChild(topPen);
    
    const bottomPen = document.createElement("div");
    bottomPen.className = "pitch-penalty-area-b";
    pitch.appendChild(bottomPen);
    
    const coords = FORMATIONS[formationName] || FORMATIONS["4-3-3"];
    
    coords.forEach(c => {
        const node = document.createElement("div");
        node.className = `player-node ${c.role.toLowerCase().substring(0, 2)}`;
        node.style.left = `${c.x}%`;
        node.style.top = `${c.y}%`;
        node.innerText = c.role;
        
        const nameLbl = document.createElement("div");
        nameLbl.className = "player-node-name";
        nameLbl.innerText = c.name;
        node.appendChild(nameLbl);
        
        pitch.appendChild(node);
    });
}

// --- Fixtures & Results View ---
function renderFixturesTable() {
    const tableBody = document.getElementById("fixtures-table-body");
    tableBody.innerHTML = "";
    
    const searchVal = document.getElementById("fixtures-search").value.toLowerCase();
    const groupFilter = document.getElementById("fixtures-group-filter").value;
    const statusFilter = document.getElementById("fixtures-status-filter").value;
    
    document.getElementById("fixtures-search").oninput = renderFixturesTable;
    document.getElementById("fixtures-group-filter").onchange = renderFixturesTable;
    document.getElementById("fixtures-status-filter").onchange = renderFixturesTable;
    
    const filteredMatches = worldCupMatches.filter(m => {
        const home = m.home.toLowerCase();
        const away = m.away.toLowerCase();
        const stage = m.stage;
        const played = m.home_score !== null && m.away_score !== null;
        
        if (searchVal && !home.includes(searchVal) && !away.includes(searchVal)) return false;
        if (groupFilter !== "ALL" && !stage.includes(`Group ${groupFilter}`)) return false;
        if (statusFilter === "PLAYED" && !played) return false;
        if (statusFilter === "UPCOMING" && played) return false;
        
        return true;
    });
    
    filteredMatches.forEach(m => {
        const row = document.createElement("tr");
        const isPlayed = m.home_score !== null && m.away_score !== null;
        const pred = getPredictionRecord(m, selectedModel);
        
        let scoreDisplay = "";
        let outcomeBadge = "-";
        
        if (isPlayed) {
            scoreDisplay = `<span class="score-cell-played">${m.home_score} - ${m.away_score}</span>`;
            
            const actualHome = parseInt(m.home_score);
            const actualAway = parseInt(m.away_score);
            const predHome = parseInt(pred.predicted_home_score);
            const predAway = parseInt(pred.predicted_away_score);
            
            const actualOutcome = actualHome > actualAway ? "H" : actualAway > actualHome ? "A" : "D";
            const predOutcome = predHome > predAway ? "H" : predAway > predHome ? "A" : "D";
            
            if (actualOutcome === predOutcome) {
                outcomeBadge = `<span class="outcome-badge outcome-correct"><i class="fa-solid fa-check"></i></span>`;
            } else {
                outcomeBadge = `<span class="outcome-badge outcome-incorrect"><i class="fa-solid fa-xmark"></i></span>`;
            }
        } else {
            scoreDisplay = `<span class="score-cell-upcoming">VS</span>`;
        }
        
        row.innerHTML = `
            <td>${m.date}</td>
            <td><span class="badge badge-group">${m.stage}</span></td>
            <td class="text-right team-cell">${m.home}</td>
            <td class="text-center">${scoreDisplay}</td>
            <td class="text-left team-cell">${m.away}</td>
            <td class="text-center text-muted" style="font-size:0.8rem;">${pred.home_xG} - ${pred.away_xG}</td>
            <td class="text-center font-bold" style="color:var(--primary-light); font-weight:700;">
                ${pred.predicted_home_score} - ${pred.predicted_away_score}
            </td>
            <td class="text-center" style="font-size:0.8rem; color:var(--text-muted);">
                ${Math.round(pred.home_win_prob * 100)}% / ${Math.round(pred.draw_prob * 100)}% / ${Math.round(pred.away_win_prob * 100)}%
            </td>
            <td class="text-center">${outcomeBadge}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// --- Groups & Standings Simulator ---
function renderGroupStandings() {
    const container = document.getElementById("groups-standings-container");
    container.innerHTML = "";
    
    const standings = computeStandings(worldCupMatches);
    
    Object.keys(standings).sort().forEach(groupLetter => {
        const groupTeams = standings[groupLetter];
        const card = document.createElement("div");
        card.className = "group-table-card glass-card";
        
        let rowsHtml = "";
        groupTeams.forEach((t, idx) => {
            const rowClass = idx < 2 ? "qualified-row-top2" : idx === 2 ? "qualified-row-3rd" : "";
            rowsHtml += `
                <tr class="${rowClass}">
                    <td class="rank-idx">${idx + 1}</td>
                    <td class="standings-team-name">${t.team}</td>
                    <td class="text-center">${t.p}</td>
                    <td class="text-center">${t.gd >= 0 ? '+' + t.gd : t.gd}</td>
                    <td class="text-center" style="font-weight:700; color:var(--primary-light);">${t.pts}</td>
                </tr>
            `;
        });
        
        card.innerHTML = `
            <h3>Group ${groupLetter}</h3>
            <table class="standings-table">
                <thead>
                    <tr>
                        <th class="text-left">#</th>
                        <th class="text-left">Team</th>
                        <th class="text-center">P</th>
                        <th class="text-center">GD</th>
                        <th class="text-center">PTS</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        `;
        
        container.appendChild(card);
    });
    
    document.getElementById("btn-simulate").onclick = () => {
        simulateRemainingMatches();
    };
}

function computeStandings(matchesList) {
    const standings = {};
    
    Object.keys(GROUPS).forEach(letter => {
        standings[letter] = GROUPS[letter].map(team => ({
            team: team, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, gd: 0, pts: 0
        }));
    });
    
    matchesList.forEach(m => {
        if (m.home_score === null || m.away_score === null) return;
        
        const groupLetter = m.stage.replace("Group ", "").trim();
        const homeScore = parseInt(m.home_score);
        const awayScore = parseInt(m.away_score);
        
        const groupTeams = standings[groupLetter];
        if (!groupTeams) return;
        
        const homeTeam = groupTeams.find(t => t.team === m.home);
        const awayTeam = groupTeams.find(t => t.team === m.away);
        
        if (!homeTeam || !awayTeam) return;
        
        homeTeam.p++;
        awayTeam.p++;
        homeTeam.gf += homeScore;
        homeTeam.ga += awayScore;
        awayTeam.gf += awayScore;
        awayTeam.ga += homeScore;
        
        if (homeScore > awayScore) {
            homeTeam.w++;
            homeTeam.pts += 3;
            awayTeam.l++;
        } else if (awayScore > homeScore) {
            awayTeam.w++;
            awayTeam.pts += 3;
            homeTeam.l++;
        } else {
            homeTeam.d++;
            homeTeam.pts += 1;
            awayTeam.d++;
            awayTeam.pts += 1;
        }
    });
    
    Object.keys(standings).forEach(letter => {
        standings[letter].forEach(t => {
            t.gd = t.gf - t.ga;
        });
        
        standings[letter].sort((a, b) => {
            if (b.pts !== a.pts) return b.pts - a.pts;
            if (b.gd !== a.gd) return b.gd - a.gd;
            if (b.gf !== a.gf) return b.gf - a.gf;
            return a.team.localeCompare(b.team);
        });
    });
    
    return standings;
}

function simulateRemainingMatches() {
    const simulatedMatches = JSON.parse(JSON.stringify(worldCupMatches));
    
    simulatedMatches.forEach(m => {
        if (m.home_score === null || m.away_score === null) {
            const pred = getPredictionRecord(m, selectedModel);
            m.home_score = pred.predicted_home_score;
            m.away_score = pred.predicted_away_score;
        }
    });
    
    const standings = computeStandings(simulatedMatches);
    const container = document.getElementById("groups-standings-container");
    container.innerHTML = "";
    
    Object.keys(standings).sort().forEach(groupLetter => {
        const groupTeams = standings[groupLetter];
        const card = document.createElement("div");
        card.className = "group-table-card glass-card animate-fade-in";
        card.style.borderColor = "var(--primary-light)";
        
        let rowsHtml = "";
        groupTeams.forEach((t, idx) => {
            const rowClass = idx < 2 ? "qualified-row-top2" : idx === 2 ? "qualified-row-3rd" : "";
            rowsHtml += `
                <tr class="${rowClass}">
                    <td class="rank-idx">${idx + 1}</td>
                    <td class="standings-team-name">${t.team}</td>
                    <td class="text-center">${t.p}</td>
                    <td class="text-center">${t.gd >= 0 ? '+' + t.gd : t.gd}</td>
                    <td class="text-center" style="font-weight:700; color:var(--primary-light);">${t.pts}</td>
                </tr>
            `;
        });
        
        card.innerHTML = `
            <h3>Group ${groupLetter} <span class="badge" style="background:var(--primary-glow); font-size:0.6rem;">SIMULATED</span></h3>
            <table class="standings-table">
                <thead>
                    <tr>
                        <th class="text-left">#</th>
                        <th class="text-left">Team</th>
                        <th class="text-center">P</th>
                        <th class="text-center">GD</th>
                        <th class="text-center">PTS</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        `;
        
        container.appendChild(card);
    });
    
    alert(`Full Group Stage simulated successfully using the ${document.getElementById("model-select").options[document.getElementById("model-select").selectedIndex].text}!`);
}

// --- TAB 4: Squad Profiles Renders ---
function renderSquadTab() {
    const teamSelect = document.getElementById("squad-team-select");
    teamSelect.onchange = () => {
        renderSquadList(teamSelect.value);
    };
    renderSquadList(teamSelect.value);
}

function renderSquadList(teamName) {
    const tableBody = document.getElementById("squad-table-body");
    const title = document.getElementById("squad-table-title");
    const formationLabel = document.getElementById("squad-formation-label");
    
    title.innerText = `${teamName} Roster & Profile`;
    tableBody.innerHTML = "";
    
    if (!modelParameters) return;
    
    const teamMeta = modelParameters.dixon_coles.teams[teamName];
    formationLabel.innerText = teamMeta.formation;
    
    renderFormationOnPitch("squad-pitch-large", teamMeta.formation);
    
    const squad = squadRosters[teamName] || [];
    if (squad.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No squad list loaded.</td></tr>`;
        return;
    }
    
    squad.forEach(p => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td class="text-center text-muted font-bold">${p.no}</td>
            <td class="team-cell" style="color:var(--text-main);">${p.name}</td>
            <td class="text-center"><span class="badge">${p.pos}</span></td>
            <td class="text-center">${p.age}</td>
            <td class="text-center">${p.caps}</td>
            <td class="text-center">${p.goals}</td>
            <td style="font-size:0.85rem; color:var(--text-muted);">${p.club}</td>
        `;
        tableBody.appendChild(row);
    });
}
