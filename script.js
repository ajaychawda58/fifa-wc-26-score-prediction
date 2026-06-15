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

// --- Global State ---
let modelParameters = null;
let worldCupMatches = [];
let squadRosters = {};

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
            
            // Trigger specific layout refreshes if needed
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
        
        // Sort matches chronologically by date and tie-break by ID
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
        // Extract team name
        const header = lines[0].replace('Squad Profile', '').trim();
        squads[header] = [];
        
        let inTable = false;
        for (let line of lines) {
            if (line.includes('| No. | Position |')) {
                inTable = true;
                continue;
            }
            if (inTable && line.startsWith('|')) {
                if (line.includes('---')) continue; // Skip header divider
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

function updateHeaderStats() {
    // Calculate overall stats
    let completedCount = 0;
    let correctOutcomeCount = 0;
    
    worldCupMatches.forEach(m => {
        if (m.home_score !== null && m.away_score !== null) {
            completedCount++;
            
            const actualHome = parseInt(m.home_score);
            const actualAway = parseInt(m.away_score);
            const predHome = parseInt(m.predicted_home_score);
            const predAway = parseInt(m.predicted_away_score);
            
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

// --- Dropdowns & selectors setup ---
function populateDropdowns() {
    if (!modelParameters) return;
    
    const teamASelect = document.getElementById("team-a-select");
    const teamBSelect = document.getElementById("team-b-select");
    const squadSelect = document.getElementById("squad-team-select");
    
    const sortedTeams = Object.keys(modelParameters.teams).sort();
    
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

// Factorial helper
const factorial = (n) => (n <= 1 ? 1 : n * factorial(n - 1));

// Poisson PMF helper
const poissonPmf = (k, lambda) => Math.exp(-lambda) * Math.pow(lambda, k) / factorial(k);

// Dixon-Coles tau adjustment helper
function getDixonColesTau(x, y, lambda, mu, rho) {
    if (x === 0 && y === 0) return 1.0 - rho * lambda * mu;
    if (x === 1 && y === 0) return 1.0 + rho * mu;
    if (x === 0 && y === 1) return 1.0 + rho * lambda;
    if (x === 1 && y === 1) return 1.0 - rho;
    return 1.0;
}

function runVisualPrediction(teamA, teamB) {
    if (!modelParameters) return;
    
    const ratingsA = modelParameters.teams[teamA];
    const ratingsB = modelParameters.teams[teamB];
    
    // Check if teamA has Home Advantage (if is host)
    const isHomeAdv = ["USA", "Canada", "Mexico"].includes(teamA);
    const haMult = isHomeAdv ? modelParameters.home_advantage_multiplier : 1.0;
    
    // Calculate expected goals (xG)
    const lambda = ratingsA.attack * ratingsB.defense * haMult;
    const mu = ratingsB.attack * ratingsA.defense;
    const rho = modelParameters.rho;
    
    // Compute score grid (max 5x5 for heatmap rendering)
    const maxGoals = 5;
    const grid = [];
    let sum = 0;
    
    for (let x = 0; x <= maxGoals; x++) {
        grid[x] = [];
        for (let y = 0; y <= maxGoals; y++) {
            let prob = poissonPmf(x, lambda) * poissonPmf(y, mu);
            let tau = getDixonColesTau(x, y, lambda, mu, rho);
            prob *= tau;
            grid[x][y] = prob;
            sum += prob;
        }
    }
    
    // Normalize grid
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            grid[x][y] /= sum;
        }
    }
    
    // Calculate outcome probabilities
    let winA = 0;
    let winB = 0;
    let draw = 0;
    
    for (let x = 0; x <= maxGoals; x++) {
        for (let y = 0; y <= maxGoals; y++) {
            if (x > y) winA += grid[x][y];
            else if (y > x) winB += grid[x][y];
            else draw += grid[x][y];
        }
    }
    
    // Find most likely score
    let maxProb = 0;
    let scoreHome = 0;
    let scoreAway = 0;
    
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
    
    // Prob bars
    const winAPercent = Math.round(winA * 100);
    const winBPercent = Math.round(winB * 100);
    const drawPercent = 100 - winAPercent - winBPercent;
    
    document.getElementById("prob-lbl-a").innerText = `${teamA}: ${winAPercent}%`;
    document.getElementById("prob-lbl-b").innerText = `${teamB}: ${winBPercent}%`;
    document.getElementById("prob-bar-a").style.width = `${winAPercent}%`;
    document.getElementById("prob-bar-b").style.width = `${winBPercent}%`;
    document.getElementById("prob-bar-draw").style.width = `${drawPercent}%`;
    
    // Predicted Score
    document.getElementById("predicted-score-text").innerText = `${scoreHome} - ${scoreAway}`;
    document.getElementById("predicted-score-prob").innerText = `Score probability: ${(maxProb * 100).toFixed(1)}%`;
    
    document.getElementById("prediction-results").style.display = "block";
    
    // Render Heatmap
    renderHeatmap(teamA, teamB, grid);
    
    // Update comparison section
    document.getElementById("comp-team-a-name").innerText = teamA;
    document.getElementById("comp-team-b-name").innerText = teamB;
    document.getElementById("comp-att-a").innerText = ratingsA.attack.toFixed(2);
    document.getElementById("comp-def-a").innerText = ratingsA.defense.toFixed(2);
    document.getElementById("comp-att-b").innerText = ratingsB.attack.toFixed(2);
    document.getElementById("comp-def-b").innerText = ratingsB.defense.toFixed(2);
    
    // Fill bars: assume attack scale 0.4 to 1.8, defense 0.4 to 1.8 (lower defense is better, invert defense fill)
    const getFillPercent = (val) => Math.min(100, Math.max(10, ((val - 0.4) / 1.4) * 100));
    const getDefFillPercent = (val) => Math.min(100, Math.max(10, (1 - (val - 0.4) / 1.4) * 100));
    
    document.getElementById("comp-att-a-bar").style.width = `${getFillPercent(ratingsA.attack)}%`;
    document.getElementById("comp-att-b-bar").style.width = `${getFillPercent(ratingsB.attack)}%`;
    document.getElementById("comp-def-a-bar").style.width = `${getDefFillPercent(ratingsA.defense)}%`;
    document.getElementById("comp-def-b-bar").style.width = `${getDefFillPercent(ratingsB.defense)}%`;
    
    document.getElementById("comp-formation-a").innerText = ratingsA.formation;
    document.getElementById("comp-formation-b").innerText = ratingsB.formation;
    
    // Render Formation Pitches
    renderFormationOnPitch("pitch-team-a", ratingsA.formation);
    renderFormationOnPitch("pitch-team-b", ratingsB.formation);
    
    document.getElementById("comparison-section").style.display = "block";
}

function renderHeatmap(teamA, teamB, grid) {
    const container = document.getElementById("heatmap-placeholder");
    container.innerHTML = "";
    
    const wrapper = document.createElement("div");
    wrapper.className = "heatmap-grid";
    
    // Empty corner cell
    const corner = document.createElement("div");
    corner.className = "heatmap-header-cell";
    corner.innerHTML = `<span style="font-size:0.7rem;">${teamA}\\${teamB}</span>`;
    wrapper.appendChild(corner);
    
    // Away goals headers (X axis)
    for (let y = 0; y <= 5; y++) {
        const cell = document.createElement("div");
        cell.className = "heatmap-header-cell";
        cell.innerText = y;
        wrapper.appendChild(cell);
    }
    
    // Grid rows
    for (let x = 0; x <= 5; x++) {
        // Home goals header (Y axis)
        const rowHeader = document.createElement("div");
        rowHeader.className = "heatmap-header-cell";
        rowHeader.innerText = x;
        wrapper.appendChild(rowHeader);
        
        for (let y = 0; y <= 5; y++) {
            const prob = grid[x][y];
            const cell = document.createElement("div");
            cell.className = "heatmap-cell";
            
            // Adjust opacity and color based on probability size
            // Pink for high probability cells
            const hue = 333; // magenta pink
            const saturation = 90;
            const lightness = 25 + Math.min(50, prob * 200); // dynamic brightness
            
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
    
    // Draw pitch lines first
    const innerCircle = document.createElement("div");
    innerCircle.className = "pitch-center-circle";
    pitch.appendChild(innerCircle);
    
    const topPen = document.createElement("div");
    topPen.className = "pitch-penalty-area-t";
    pitch.appendChild(topPen);
    
    const bottomPen = document.createElement("div");
    bottomPen.className = "pitch-penalty-area-b";
    pitch.appendChild(bottomPen);
    
    // Get positions
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
    
    // Filters
    const searchVal = document.getElementById("fixtures-search").value.toLowerCase();
    const groupFilter = document.getElementById("fixtures-group-filter").value;
    const statusFilter = document.getElementById("fixtures-status-filter").value;
    
    // Apply filters and event listeners
    document.getElementById("fixtures-search").oninput = renderFixturesTable;
    document.getElementById("fixtures-group-filter").onchange = renderFixturesTable;
    document.getElementById("fixtures-status-filter").onchange = renderFixturesTable;
    
    const filteredMatches = worldCupMatches.filter(m => {
        const home = m.home.toLowerCase();
        const away = m.away.toLowerCase();
        const stage = m.stage;
        const played = m.home_score !== null && m.away_score !== null;
        
        // Search filter
        if (searchVal && !home.includes(searchVal) && !away.includes(searchVal)) return false;
        
        // Group filter
        if (groupFilter !== "ALL" && !stage.includes(`Group ${groupFilter}`)) return false;
        
        // Status filter
        if (statusFilter === "PLAYED" && !played) return false;
        if (statusFilter === "UPCOMING" && played) return false;
        
        return true;
    });
    
    filteredMatches.forEach(m => {
        const row = document.createElement("tr");
        
        const isPlayed = m.home_score !== null && m.away_score !== null;
        
        // Columns: Date, Stage, Home, Score, Away, xG, Prediction, Win Probs, Outcome
        let scoreDisplay = "";
        let outcomeBadge = "-";
        
        if (isPlayed) {
            scoreDisplay = `<span class="score-cell-played">${m.home_score} - ${m.away_score}</span>`;
            
            // Check result accuracy
            const actualHome = parseInt(m.home_score);
            const actualAway = parseInt(m.away_score);
            const predHome = parseInt(m.predicted_home_score);
            const predAway = parseInt(m.predicted_away_score);
            
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
            <td class="text-center text-muted" style="font-size:0.8rem;">${m.home_xG} - ${m.away_xG}</td>
            <td class="text-center font-bold" style="color:var(--primary-light); font-weight:700;">
                ${m.predicted_home_score} - ${m.predicted_away_score}
            </td>
            <td class="text-center" style="font-size:0.8rem; color:var(--text-muted);">
                ${Math.round(m.home_win_prob * 100)}% / ${Math.round(m.draw_prob * 100)}% / ${Math.round(m.away_win_prob * 100)}%
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
    
    // We compute the standings dynamically based on played results
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
    
    // Set simulator button listener
    document.getElementById("btn-simulate").onclick = () => {
        simulateRemainingMatches();
    };
}

function computeStandings(matchesList) {
    const standings = {};
    
    // Initialize teams
    Object.keys(GROUPS).forEach(letter => {
        standings[letter] = GROUPS[letter].map(team => ({
            team: team, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, gd: 0, pts: 0
        }));
    });
    
    // Update standings with scores
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
    
    // Compute goal difference and sort
    Object.keys(standings).forEach(letter => {
        standings[letter].forEach(t => {
            t.gd = t.gf - t.ga;
        });
        
        // Sort: Points DESC, Goal Difference DESC, Goals For DESC, alphabetical
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
    // Clone matches
    const simulatedMatches = JSON.parse(jsonStringify(worldCupMatches));
    
    simulatedMatches.forEach(m => {
        if (m.home_score === null || m.away_score === null) {
            // Fill in scores using predicted score
            m.home_score = m.predicted_home_score;
            m.away_score = m.predicted_away_score;
        }
    });
    
    // Compute simulated standings
    const standings = computeStandings(simulatedMatches);
    
    // Update container in UI
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
    
    // Highlight completed simulation
    alert("Full Group Stage simulated successfully based on Bayesian expected scores!");
}

function jsonStringify(obj) {
    return JSON.stringify(obj);
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
    
    const teamMeta = modelParameters.teams[teamName];
    formationLabel.innerText = teamMeta.formation;
    
    // Render Formation Pitch
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
