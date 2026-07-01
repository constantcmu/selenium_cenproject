// Configuration
const API_BASE_URL = "http://127.0.0.1:8000";

// Default State for Nodes
let nodes = [
    { id: "node-source", type: "source", title: "1. แหล่งข้อมูลงบประมาณ", x: 60, y: 160, data: { year: "2025", excel: "table_main_2568.xlsx" } },
    { id: "node-scraper", type: "scraper", title: "2. บอตสแกนเนอร์ (main.py)", x: 420, y: 60, data: {} },
    { id: "node-filter", type: "filter", title: "3. เงื่อนไขโครงการ", x: 420, y: 300, data: { percent: "100" } },
    { id: "node-disburse", type: "disburse", title: "4. บอตคีย์เบิกจ่าย", x: 780, y: 200, data: {} },
    { id: "node-console", type: "console", title: "5. บันทึกผลลัพธ์ (Terminal Logs)", x: 1140, y: 110, data: {} }
];

// Connection definition (Fixed flow graph mapping ports, can be dynamically modified)
let connections = [
    { from: "node-source", to: "node-scraper" },
    { from: "node-source", to: "node-filter" },
    { from: "node-scraper", to: "node-disburse" },
    { from: "node-filter", to: "node-disburse" },
    { from: "node-disburse", to: "node-console" },
    { from: "node-scraper", to: "node-console" }
];

// State variables
let activeDraggingNode = null;
let dragOffset = { x: 0, y: 0 };
let activeJobStates = {
    budget_tracker: false,
    disbursement_system: false
};

// Zoom and Pan State
let panX = 0;
let panY = 0;
let zoom = 1.0;
let isPanning = false;
let panStart = { x: 0, y: 0 };

// Connecting state
let connectingSourceNodeId = null;

// DOM Elements
const canvasContainer = document.getElementById("canvas-container");
const canvasViewport = document.getElementById("canvas-viewport");
const nodesLayer = document.getElementById("nodes-layer");
const connectionsSvg = document.getElementById("connections-svg");
const btnRunWorkflow = document.getElementById("btn-run-workflow");
const btnResetLayout = document.getElementById("btn-reset-layout");
const apiDot = document.getElementById("api-dot");
const apiText = document.getElementById("api-text");

// Zoom controls
const btnZoomIn = document.getElementById("btn-zoom-in");
const btnZoomOut = document.getElementById("btn-zoom-out");
const btnZoomReset = document.getElementById("btn-zoom-reset");

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    initNodes();
    drawConnections();
    startStatusPolling();
    setupCanvasDragAndDrop();
    setupCanvasZoomAndPan();

    // Event Listeners
    btnRunWorkflow.addEventListener("click", runEntireWorkflow);
    btnResetLayout.addEventListener("click", resetNodeLayout);
    
    // Zoom Buttons
    btnZoomIn.addEventListener("click", () => adjustZoom(1.15));
    btnZoomOut.addEventListener("click", () => adjustZoom(0.85));
    btnZoomReset.addEventListener("click", () => {
        zoom = 1.0;
        panX = 0;
        panY = 0;
        updateViewportTransform();
        btnZoomReset.innerText = "100%";
    });

    // Window Resize listener to update curves
    window.addEventListener("resize", drawConnections);
    
    // Cancel connecting state if clicked outside ports
    canvasContainer.addEventListener("click", (e) => {
        if (!e.target.classList.contains("port-handle")) {
            cancelConnecting();
        }
    });
});

// Render Nodes to DOM
function initNodes() {
    nodesLayer.innerHTML = "";
    nodes.forEach(node => {
        const nodeEl = createNodeElement(node);
        nodesLayer.appendChild(nodeEl);
    });
}

// Helper to create HTML for individual nodes
function createNodeElement(node) {
    const card = document.createElement("div");
    card.className = `flow-node ${node.type}-node`;
    card.id = node.id;
    card.style.left = `${node.x}px`;
    card.style.top = `${node.y}px`;

    // Dynamic Icon
    let headerIcon = "fa-cube";
    if (node.type === "source") headerIcon = "fa-file-excel";
    else if (node.type === "scraper") headerIcon = "fa-spider";
    else if (node.type === "filter") headerIcon = "fa-filter";
    else if (node.type === "disburse") headerIcon = "fa-wallet";
    else if (node.type === "console") headerIcon = "fa-terminal";

    // Card Header
    const header = document.createElement("div");
    header.className = "node-header";
    header.innerHTML = `
        <i class="fa-solid ${headerIcon}"></i>
        <h4 class="node-title" title="ดับเบิ้ลคลิกเพื่อเปลี่ยนชื่อ">${node.title}</h4>
        <button class="btn-delete-node" title="ลบโหนด"><i class="fa-solid fa-xmark"></i></button>
    `;
    card.appendChild(header);

    // Double click to rename node title
    const titleEl = header.querySelector(".node-title");
    titleEl.addEventListener("dblclick", () => {
        const newTitle = prompt("กรุณาระบุชื่อโหนดใหม่:", node.title);
        if (newTitle && newTitle.trim()) {
            node.title = newTitle.trim();
            titleEl.innerText = node.title;
        }
    });

    // Delete node button listener
    const deleteBtn = header.querySelector(".btn-delete-node");
    deleteBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm(`คุณต้องการลบโหนด "${node.title}" หรือไม่?`)) {
            // Remove node from state
            nodes = nodes.filter(n => n.id !== node.id);
            // Remove all associated connections
            connections = connections.filter(c => c.from !== node.id && c.to !== node.id);
            initNodes();
            drawConnections();
        }
    });

    // Card Body Content
    const body = document.createElement("div");
    body.className = "node-body";

    if (node.type === "source") {
        body.innerHTML = `
            <div class="node-input-group">
                <label>ปีงบประมาณ</label>
                <select class="node-select" id="source-year-select-${node.id}">
                    <option value="2025" ${node.data.year === "2025" ? "selected" : ""}>2568 (พ.ร.บ. 2568)</option>
                    <option value="2026" ${node.data.year === "2026" ? "selected" : ""}>2569 (พ.ร.บ. 2569)</option>
                </select>
            </div>
            <div class="node-input-group">
                <label>ชื่อไฟล์ตรวจสอบ (Excel)</label>
                <input class="node-input" type="text" id="source-excel-input-${node.id}" value="${node.data.excel || ''}">
            </div>
        `;
        // Attach listener to update local state
        setTimeout(() => {
            const yearSelect = document.getElementById(`source-year-select-${node.id}`);
            const excelInput = document.getElementById(`source-excel-input-${node.id}`);
            if (yearSelect && excelInput) {
                yearSelect.addEventListener("change", (e) => {
                    node.data.year = e.target.value;
                    if (e.target.value === "2026") {
                        excelInput.value = "table_main_2569.xlsx";
                        node.data.excel = "table_main_2569.xlsx";
                    } else {
                        excelInput.value = "table_main_2568.xlsx";
                        node.data.excel = "table_main_2568.xlsx";
                    }
                });
                excelInput.addEventListener("input", (e) => {
                    node.data.excel = e.target.value;
                });
            }
        }, 0);
    } 
    else if (node.type === "scraper") {
        body.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>สถานะระบบ:</span>
                <span class="badge-status idle" id="node-scraper-badge">Idle</span>
            </div>
            <button class="btn-primary" style="padding: 6px 12px; font-size:11px; margin-top:4px;" onclick="runSingleBot('scraper')">
                <i class="fa-solid fa-play"></i> เริ่มสแกนโครงการ
            </button>
        `;
    } 
    else if (node.type === "filter") {
        body.innerHTML = `
            <div class="node-input-group">
                <label>เงื่อนไขคัดกรอง</label>
                <div style="display:flex; align-items:center; gap:8px; margin-top:4px;">
                    <i class="fa-solid fa-percent" style="color:var(--text-muted)"></i>
                    <span>เบิกจ่ายจริง &lt; 100%</span>
                </div>
            </div>
        `;
    } 
    else if (node.type === "disburse") {
        body.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>สถานะระบบ:</span>
                <span class="badge-status idle" id="node-disburse-badge">Idle</span>
            </div>
            <button class="btn-primary" style="padding: 6px 12px; font-size:11px; margin-top:4px; background:linear-gradient(135deg, #4f46e5, #a855f7); box-shadow:0 0 10px rgba(168, 85, 247, 0.2)" onclick="runSingleBot('disburse')">
                <i class="fa-solid fa-play"></i> เริ่มคีย์เบิกจ่าย
            </button>
        `;
    } 
    else if (node.type === "console") {
        body.innerHTML = `
            <div class="node-input-group">
                <label>Realtime Terminal Console</label>
                <div class="console-output" id="live-console">Waiting for workflow start...</div>
            </div>
        `;
    }

    card.appendChild(body);

    // Port Handles (Input/Output handles)
    const portsContainer = document.createElement("div");
    portsContainer.className = "node-ports";
    
    // All nodes except source have inputs
    if (node.type !== "source") {
        const inputPort = document.createElement("div");
        inputPort.className = "port-handle port-input";
        inputPort.setAttribute("data-port-type", "input");
        inputPort.addEventListener("click", (e) => handlePortClick(e, node.id, "input"));
        portsContainer.appendChild(inputPort);
    }
    
    // All nodes except console have outputs
    if (node.type !== "console") {
        const outputPort = document.createElement("div");
        outputPort.className = "port-handle port-output";
        outputPort.setAttribute("data-port-type", "output");
        outputPort.addEventListener("click", (e) => handlePortClick(e, node.id, "output"));
        portsContainer.appendChild(outputPort);
    }

    card.appendChild(portsContainer);

    // Make node draggable
    setupNodeDrag(card, header, node);

    return card;
}

// Drag and drop mechanics for nodes with Zoom correction
function setupNodeDrag(nodeElement, headerElement, nodeState) {
    headerElement.addEventListener("mousedown", (e) => {
        // Prevent default actions and drag events bubbles to container
        e.preventDefault();
        e.stopPropagation();
        
        activeDraggingNode = nodeElement;
        nodeElement.classList.add("dragging");

        // Record start mouse and node position
        const startX = e.clientX;
        const startY = e.clientY;
        const startNodeX = nodeState.x;
        const startNodeY = nodeState.y;

        // MouseMove and MouseUp listeners
        const onMouseMove = (moveEvent) => {
            if (!activeDraggingNode) return;
            
            // ZOOM CORRECTION: divide mouse movement delta by current scale zoom
            let x = startNodeX + (moveEvent.clientX - startX) / zoom;
            let y = startNodeY + (moveEvent.clientY - startY) / zoom;

            // Constrain nodes inside virtual viewport
            x = Math.max(10, Math.min(4700, x));
            y = Math.max(10, Math.min(4700, y));

            // Update UI
            activeDraggingNode.style.left = `${x}px`;
            activeDraggingNode.style.top = `${y}px`;

            // Update state
            nodeState.x = x;
            nodeState.y = y;

            // Re-render connection curves
            drawConnections();
        };

        const onMouseUp = () => {
            if (activeDraggingNode) {
                activeDraggingNode.classList.remove("dragging");
                activeDraggingNode = null;
            }
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    });
}

// SVG bezier curves render
function drawConnections() {
    connectionsSvg.innerHTML = "";
    
    connections.forEach((conn, index) => {
        const fromNode = document.getElementById(conn.from);
        const toNode = document.getElementById(conn.to);
        
        if (!fromNode || !toNode) return;

        // Get output handle of source and input handle of target
        const fromOutputHandle = fromNode.querySelector(".port-output");
        const toInputHandle = toNode.querySelector(".port-input");

        if (!fromOutputHandle || !toInputHandle) return;

        // Get relative offset positions to canvas-viewport (which has scale transform applied)
        // Offset relative to parent is safer because both are inside canvas-viewport
        const x1 = fromNode.offsetLeft + fromNode.offsetWidth;
        const y1 = fromNode.offsetTop + (fromNode.offsetHeight / 2);
        
        const x2 = toNode.offsetLeft;
        const y2 = toNode.offsetTop + (toNode.offsetHeight / 2);

        // Control curve shape
        const controlOffset = Math.abs(x2 - x1) * 0.45;
        const pathData = `M ${x1} ${y1} C ${x1 + controlOffset} ${y1}, ${x2 - controlOffset} ${y2}, ${x2} ${y2}`;

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        path.setAttribute("class", "connection-curve");
        path.setAttribute("title", "ดับเบิ้ลคลิกเส้นเพื่อลบการเชื่อมต่อ");
        
        // Active flowing flow animation
        const scraperRunning = activeJobStates.budget_tracker;
        const disburseRunning = activeJobStates.disbursement_system;
        
        if ((conn.from === "node-source" && conn.to === "node-scraper" && scraperRunning) ||
            (conn.from === "node-scraper" && conn.to === "node-disburse" && scraperRunning) ||
            (conn.from === "node-scraper" && conn.to === "node-console" && scraperRunning) ||
            (conn.from === "node-source" && conn.to === "node-filter" && disburseRunning) ||
            (conn.from === "node-filter" && conn.to === "node-disburse" && disburseRunning) ||
            (conn.from === "node-disburse" && conn.to === "node-console" && disburseRunning)) {
            path.classList.add("active");
        }

        // Double click connection to delete it
        path.addEventListener("dblclick", (e) => {
            e.stopPropagation();
            if (confirm("คุณต้องการลบเส้นการเชื่อมต่อนี้หรือไม่?")) {
                connections.splice(index, 1);
                drawConnections();
            }
        });

        connectionsSvg.appendChild(path);
    });
}

// Click to connect system (สามารถเชื่อมโยงเปลี่ยนโหนดได้อิสระ)
function handlePortClick(e, nodeId, portType) {
    e.stopPropagation();
    
    if (portType === "output") {
        // Start connection
        connectingSourceNodeId = nodeId;
        // Visual indicator
        const handle = e.target;
        handle.style.backgroundColor = "var(--warning)";
        handle.style.borderColor = "var(--warning)";
        
        // Show status
        const consoleEl = document.getElementById("live-console");
        if (consoleEl) {
            consoleEl.innerText += `\n[System] เลือกโหนดต้นทาง: ${nodes.find(n => n.id === nodeId).title} -> เลือกพอร์ตสีเขียวของโหนดปลายทางเพื่อเชื่อมต่อ...`;
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }
    } 
    else if (portType === "input" && connectingSourceNodeId) {
        // Complete connection
        const sourceNodeId = connectingSourceNodeId;
        
        // Check if connection already exists
        const exists = connections.some(c => c.from === sourceNodeId && c.to === nodeId);
        if (exists) {
            alert("เส้นเชื่อมนี้มีอยู่แล้ว!");
        } else if (sourceNodeId === nodeId) {
            alert("ไม่สามารถเชื่อมต่อหาโหนดตัวเองได้!");
        } else {
            // Save connection
            connections.push({ from: sourceNodeId, to: nodeId });
            drawConnections();
        }
        cancelConnecting();
    }
}

function cancelConnecting() {
    connectingSourceNodeId = null;
    // Reset all output port colors
    document.querySelectorAll(".port-output").forEach(p => {
        p.style.backgroundColor = "";
        p.style.borderColor = "";
    });
}

// Drag and drop from sidebar library
function setupCanvasDragAndDrop() {
    const paletteItems = document.querySelectorAll(".palette-item");
    
    paletteItems.forEach(item => {
        item.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("text/plain", e.target.getAttribute("data-node-type"));
        });
    });

    canvasContainer.addEventListener("dragover", (e) => {
        e.preventDefault();
    });

    canvasContainer.addEventListener("drop", (e) => {
        e.preventDefault();
        const nodeType = e.dataTransfer.getData("text/plain");
        if (!nodeType) return;

        const containerRect = canvasContainer.getBoundingClientRect();
        // Calculate coords inside the zoom/panned viewport
        const dropX = (e.clientX - containerRect.left - panX) / zoom - 140;
        const dropY = (e.clientY - containerRect.top - panY) / zoom - 80;

        let title = "โหนดใหม่";
        if (nodeType === "source") title = "ข้อมูลตารางหลัก";
        else if (nodeType === "scraper") title = "บอต Scraper เสริม";
        else if (nodeType === "filter") title = "เงื่อนไขโครงการเสริม";
        else if (nodeType === "disburse") title = "บอตคีย์เบิกจ่ายเสริม";
        else if (nodeType === "console") title = "Terminal logs";

        const newNodeId = `node-custom-${Date.now()}`;
        const newNode = {
            id: newNodeId,
            type: nodeType,
            title: `${title} (${nodes.length + 1})`,
            x: Math.max(10, dropX),
            y: Math.max(10, dropY),
            data: {}
        };

        nodes.push(newNode);
        initNodes();
        drawConnections();
    });
}

// Zoom and Pan implementation
function setupCanvasZoomAndPan() {
    canvasContainer.addEventListener("mousedown", (e) => {
        // Start pan only when clicking the container background directly
        if (e.target === canvasContainer || e.target === canvasViewport || e.target.id === "connections-svg") {
            isPanning = true;
            canvasContainer.classList.add("panning");
            panStart.x = e.clientX - panX;
            panStart.y = e.clientY - panY;
            e.preventDefault();
        }
    });

    document.addEventListener("mousemove", (e) => {
        if (isPanning) {
            panX = e.clientX - panStart.x;
            panY = e.clientY - panStart.y;
            updateViewportTransform();
        }
    });

    document.addEventListener("mouseup", () => {
        if (isPanning) {
            isPanning = false;
            canvasContainer.classList.remove("panning");
        }
    });

    // Zoom on mouse wheel scroll
    canvasContainer.addEventListener("wheel", (e) => {
        e.preventDefault();
        
        const zoomFactor = 1.1;
        let newZoom = zoom;
        
        if (e.deltaY < 0) {
            newZoom = Math.min(2.0, zoom * zoomFactor);
        } else {
            newZoom = Math.max(0.4, zoom / zoomFactor);
        }

        // Centered zoom correction
        const containerRect = canvasContainer.getBoundingClientRect();
        const mouseX = e.clientX - containerRect.left;
        const mouseY = e.clientY - containerRect.top;

        // Keep viewport point under cursor at the same screen point
        panX = mouseX - (mouseX - panX) * (newZoom / zoom);
        panY = mouseY - (mouseY - panY) * (newZoom / zoom);
        
        zoom = newZoom;
        updateViewportTransform();
    }, { passive: false });
}

function adjustZoom(factor) {
    const newZoom = Math.max(0.4, Math.min(2.0, zoom * factor));
    
    // Zoom relative to center of canvas container
    const containerRect = canvasContainer.getBoundingClientRect();
    const centerX = containerRect.width / 2;
    const centerY = containerRect.height / 2;

    panX = centerX - (centerX - panX) * (newZoom / zoom);
    panY = centerY - (centerY - panY) * (newZoom / zoom);

    zoom = newZoom;
    updateViewportTransform();
}

function updateViewportTransform() {
    canvasViewport.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    btnZoomReset.innerText = `${Math.round(zoom * 100)}%`;
}

// Reset node positions to default
function resetNodeLayout() {
    zoom = 1.0;
    panX = 0;
    panY = 0;
    updateViewportTransform();
    
    nodes = [
        { id: "node-source", type: "source", title: "1. แหล่งข้อมูลงบประมาณ", x: 60, y: 160, data: { year: "2025", excel: "table_main_2568.xlsx" } },
        { id: "node-scraper", type: "scraper", title: "2. บอตสแกนเนอร์ (main.py)", x: 420, y: 60, data: {} },
        { id: "node-filter", type: "filter", title: "3. เงื่อนไขโครงการ", x: 420, y: 300, data: { percent: "100" } },
        { id: "node-disburse", type: "disburse", title: "4. บอตคีย์เบิกจ่าย", x: 780, y: 200, data: {} },
        { id: "node-console", type: "console", title: "5. บันทึกผลลัพธ์ (Terminal Logs)", x: 1140, y: 110, data: {} }
    ];
    connections = [
        { from: "node-source", to: "node-scraper" },
        { from: "node-source", to: "node-filter" },
        { from: "node-scraper", to: "node-disburse" },
        { from: "node-filter", to: "node-disburse" },
        { from: "node-disburse", to: "node-console" },
        { from: "node-scraper", to: "node-console" }
    ];
    initNodes();
    drawConnections();
}

// Run single bot action (Scraper or Disburse)
async function runSingleBot(botType) {
    const sourceNode = nodes.find(n => n.type === "source");
    const year = sourceNode ? sourceNode.data.year : "2025";
    const excel = sourceNode ? sourceNode.data.excel : "table_main_2568.xlsx";

    try {
        let endpoint = "";
        let body = {};
        
        if (botType === "scraper") {
            endpoint = "/api/run/budget-tracker";
            body = { budget_year: year, excel_file: excel };
            const el = document.getElementById("node-scraper");
            if (el) el.classList.add("active-job");
        } else {
            endpoint = "/api/run/disbursement";
            const el = document.getElementById("node-disburse");
            if (el) el.classList.add("active-job");
        }

        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const data = await res.json();
        
        const consoleEl = document.getElementById("live-console");
        if (consoleEl) {
            consoleEl.innerText += `\n\n[System] สั่งเริ่มงานบอต ${botType}... (${new Date().toLocaleTimeString()})\n${data.message}`;
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }

        setTimeout(pollStatusOnce, 500);

    } catch (err) {
        console.error("Failed to run bot:", err);
        alert(`เกิดข้อผิดพลาดในการเชื่อมต่อ API: ${err.message}`);
    }
}

// Run entire workflow sequentially (Scraper first, then Disbursement)
async function runEntireWorkflow() {
    const consoleEl = document.getElementById("live-console");
    if (consoleEl) {
        consoleEl.innerText = "[System] เริ่มการประมวลผลทั้งระบบอัตโนมัติ...";
    }
    await runSingleBot("scraper");
}

// Polling FastAPI Server Status
async function pollStatusOnce() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/status`);
        const status = await res.json();
        
        // API online
        apiDot.className = "status-dot green";
        apiText.innerText = "API Online (127.0.0.1:8000)";

        // Read states
        activeJobStates.budget_tracker = status.jobs.budget_tracker.running;
        activeJobStates.disbursement_system = status.jobs.disbursement_system.running;

        // Update sidebar badges
        const sidebarScraperBadge = document.getElementById("monitor-scraper-status");
        const sidebarDisburseBadge = document.getElementById("monitor-disburse-status");
        
        updateBadge(sidebarScraperBadge, status.jobs.budget_tracker);
        updateBadge(sidebarDisburseBadge, status.jobs.disbursement_system);

        // Update Node specific Badges and Glowing outlines
        const nodeScraper = document.getElementById("node-scraper");
        const nodeDisburse = document.getElementById("node-disburse");
        const nodeScraperBadge = document.getElementById("node-scraper-badge");
        const nodeDisburseBadge = document.getElementById("node-disburse-badge");

        if (nodeScraper && nodeScraperBadge) {
            updateBadge(nodeScraperBadge, status.jobs.budget_tracker);
            if (activeJobStates.budget_tracker) nodeScraper.classList.add("active-job");
            else nodeScraper.classList.remove("active-job");
        }

        if (nodeDisburse && nodeDisburseBadge) {
            updateBadge(nodeDisburseBadge, status.jobs.disbursement_system);
            if (activeJobStates.disbursement_system) nodeDisburse.classList.add("active-job");
            else nodeDisburse.classList.remove("active-job");
        }

        // Draw connections to reflect active glowing flows
        drawConnections();

        // Update Console Logs
        const consoleEl = document.getElementById("live-console");
        if (consoleEl) {
            let combinedLogs = "";
            if (activeJobStates.budget_tracker || (!activeJobStates.budget_tracker && status.logs.budget_tracker)) {
                combinedLogs += `--- LOGS: BUDGET TRACKER SCRAPER ---\n${status.logs.budget_tracker}\n`;
            }
            if (activeJobStates.disbursement_system || (!activeJobStates.disbursement_system && status.logs.disbursement_system)) {
                combinedLogs += `\n--- LOGS: DISBURSEMENT FORM FILLER ---\n${status.logs.disbursement_system}\n`;
            }

            if (combinedLogs.trim()) {
                consoleEl.innerText = combinedLogs;
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

    } catch (err) {
        // API Offline
        apiDot.className = "status-dot red";
        apiText.innerText = "API Connection Failed (Offline)";
        
        const badge1 = document.getElementById("monitor-scraper-status");
        const badge2 = document.getElementById("monitor-disburse-status");
        if (badge1) { badge1.className = "badge-status error"; badge1.innerText = "Offline"; }
        if (badge2) { badge2.className = "badge-status error"; badge2.innerText = "Offline"; }
    }
}

function updateBadge(element, jobState) {
    if (!element) return;
    if (jobState.running) {
        element.className = "badge-status running";
        element.innerText = "Running";
    } else if (jobState.error) {
        element.className = "badge-status error";
        element.innerText = "Error";
    } else if (jobState.last_run !== null || element.innerText === "Running" || element.innerText === "Success") {
        element.className = "badge-status success";
        element.innerText = "Success";
    } else {
        element.className = "badge-status idle";
        element.innerText = "Idle";
    }
}

// Poll state every 2 seconds
function startStatusPolling() {
    pollStatusOnce();
    setInterval(pollStatusOnce, 2000);
}
