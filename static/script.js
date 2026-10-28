/**
 * WARDHAN TRADING EST. — Quotation Generator
 * Client-Side Calculations, Multi-Filters, Live Preview Sync & Document Generator
 */

// Helper: Convert integer to English words
function integerToWords(num) {
    if (num === 0) return "Zero";
    const ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                  "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                  "Seventeen", "Eighteen", "Nineteen"];
    const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
    const thousands = ["", "Thousand", "Million", "Billion"];

    function processChunk(n) {
        let parts = [];
        if (n >= 100) {
            parts.push(ones[Math.floor(n / 100)] + " Hundred");
            n %= 100;
        }
        if (n >= 20) {
            parts.push(tens[Math.floor(n / 10)]);
            n %= 10;
        }
        if (n > 0) {
            parts.push(ones[n]);
        }
        return parts.join(" ");
    }

    let chunks = [];
    let chunkIdx = 0;
    let temp = num;
    while (temp > 0) {
        let chunk = temp % 1000;
        if (chunk !== 0) {
            let chunkStr = processChunk(chunk);
            if (thousands[chunkIdx]) {
                chunkStr += " " + thousands[chunkIdx];
            }
            chunks.push(chunkStr);
        }
        temp = Math.floor(temp / 1000);
        chunkIdx++;
    }

    return chunks.reverse().join(" ").trim();
}

// Convert KD and Fils to Kuwait Currency words
function amountToWords(kd, fils) {
    let kdStr = kd > 0 ? integerToWords(kd) : "";
    let res = kdStr ? `KD ${kdStr}` : (fils === 0 ? "KD Zero" : "");

    if (fils > 0) {
        let filsStr = integerToWords(fils);
        if (res) {
            res += ` and ${filsStr} Fils`;
        } else {
            res = `${filsStr} Fils`;
        }
    }
    return res || "KD Zero";
}

// Global mobile editor tab switch function
window.switchEditorTab = function(target) {
    const layout = document.querySelector(".editor-layout");
    const tabBtnForm = document.getElementById("tabBtnForm");
    const tabBtnPreview = document.getElementById("tabBtnPreview");

    if (!layout) return;

    if (target === "preview") {
        layout.classList.add("show-preview");
        tabBtnForm?.classList.remove("active");
        tabBtnPreview?.classList.add("active");
    } else {
        layout.classList.remove("show-preview");
        tabBtnForm?.classList.add("active");
        tabBtnPreview?.classList.remove("active");
    }
};

// Global form submit loading state
window.handleFormSubmit = function(form) {
    const btn = document.getElementById("saveQuotationBtn");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                <path d="M12 2a10 10 0 0 1 10 10"></path>
            </svg>
            <span>Saving &amp; Generating...</span>
        `;
    }
    return true;
};

document.addEventListener("DOMContentLoaded", () => {
    // -----------------------------------------------------------------------
    // 1. Dark / Light Mode Switcher
    // -----------------------------------------------------------------------
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("wt-theme", newTheme);
        });
    }

    // -----------------------------------------------------------------------
    // 2. Mobile Navigation Menu Drawer
    // -----------------------------------------------------------------------
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const mobileDrawer = document.getElementById("mobileDrawer");

    if (mobileMenuBtn && mobileDrawer) {
        mobileMenuBtn.addEventListener("click", () => {
            const isOpen = mobileDrawer.classList.toggle("open");
            mobileMenuBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
            const openIcon = mobileMenuBtn.querySelector(".menu-open-icon");
            const closeIcon = mobileMenuBtn.querySelector(".menu-close-icon");
            if (openIcon && closeIcon) {
                openIcon.style.display = isOpen ? "none" : "block";
                closeIcon.style.display = isOpen ? "block" : "none";
            }
        });
    }

    // -----------------------------------------------------------------------
    // 3. Dashboard Multi-Filter Engine
    // -----------------------------------------------------------------------
    const filterSearch = document.getElementById("filterSearch");
    const filterCustomer = document.getElementById("filterCustomer");
    const filterMinAmount = document.getElementById("filterMinAmount");
    const filterMaxAmount = document.getElementById("filterMaxAmount");
    const clearFiltersBtn = document.getElementById("clearFiltersBtn");
    const matchingCountLabel = document.getElementById("matchingCountLabel");
    const noFilterMatch = document.getElementById("noFilterMatch");
    const quotationRows = document.querySelectorAll(".quotation-row");
    const totalRecords = quotationRows.length;

    function applyDashboardFilters() {
        if (quotationRows.length === 0) return;

        const query = (filterSearch?.value || "").toLowerCase().trim();
        const selectedCustomer = (filterCustomer?.value || "").toLowerCase().trim();
        const minAmt = parseFloat(filterMinAmount?.value);
        const maxAmt = parseFloat(filterMaxAmount?.value);

        let visibleCount = 0;

        quotationRows.forEach((row) => {
            const qno = (row.dataset.qno || "").toLowerCase();
            const customer = (row.dataset.customer || "").toLowerCase();
            const items = (row.dataset.items || "").toLowerCase();
            const amount = parseFloat(row.dataset.amount || 0);

            let matchesSearch = true;
            if (query) {
                matchesSearch = qno.includes(query) || customer.includes(query) || items.includes(query);
            }

            let matchesCustomer = true;
            if (selectedCustomer) {
                matchesCustomer = customer === selectedCustomer;
            }

            let matchesMin = true;
            if (!isNaN(minAmt)) {
                matchesMin = amount >= minAmt;
            }

            let matchesMax = true;
            if (!isNaN(maxAmt)) {
                matchesMax = amount <= maxAmt;
            }

            if (matchesSearch && matchesCustomer && matchesMin && matchesMax) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });

        if (matchingCountLabel) {
            matchingCountLabel.textContent = `Showing ${visibleCount} of ${totalRecords} records`;
        }

        if (noFilterMatch) {
            noFilterMatch.style.display = visibleCount === 0 && totalRecords > 0 ? "block" : "none";
        }
    }

    if (filterSearch) filterSearch.addEventListener("input", applyDashboardFilters);
    if (filterCustomer) filterCustomer.addEventListener("change", applyDashboardFilters);
    if (filterMinAmount) filterMinAmount.addEventListener("input", applyDashboardFilters);
    if (filterMaxAmount) filterMaxAmount.addEventListener("input", applyDashboardFilters);

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener("click", () => {
            if (filterSearch) filterSearch.value = "";
            if (filterCustomer) filterCustomer.value = "";
            if (filterMinAmount) filterMinAmount.value = "";
            if (filterMaxAmount) filterMaxAmount.value = "";
            applyDashboardFilters();
        });
    }

    // -----------------------------------------------------------------------
    // 4. Quotation Form Editor & Live Paper Preview
    // -----------------------------------------------------------------------
    const quotationForm = document.getElementById("quotationForm");
    const itemsContainer = document.getElementById("itemsContainer") || document.getElementById("itemsTableBody");
    const addItemBtn = document.getElementById("addItemBtn");

    let isCustomWordsEdited = false;

    function updateItemNumbers() {
        if (!itemsContainer) return;
        const rows = itemsContainer.querySelectorAll(".item-row");
        rows.forEach((row, index) => {
            const badge = row.querySelector(".item-index");
            if (badge) badge.textContent = index + 1;
        });
    }

    if (quotationForm && itemsContainer) {
        const wordsInput = document.getElementById("amount_in_words");
        if (wordsInput) {
            wordsInput.addEventListener("input", () => {
                isCustomWordsEdited = true;
                updatePreview();
            });
        }

        if (addItemBtn) {
            addItemBtn.addEventListener("click", () => {
                addItemRow();
                recalculate();
            });
        }

        itemsContainer.addEventListener("click", (e) => {
            const removeBtn = e.target.closest(".remove-item-btn");
            if (removeBtn) {
                const rows = itemsContainer.querySelectorAll(".item-row");
                if (rows.length > 1) {
                    removeBtn.closest(".item-row").remove();
                    updateItemNumbers();
                    recalculate();
                } else {
                    alert("A quotation must have at least one item.");
                }
            }
        });

        quotationForm.addEventListener("input", (e) => {
            const target = e.target;
            if (target.classList.contains("calc-trigger")) {
                const row = target.closest(".item-row");
                if (row) {
                    // Manual edit of Total price per piece
                    if (target.classList.contains("item-tkd") || target.classList.contains("item-tfills")) {
                        row.dataset.manualTotal = "true";
                    } else if (target.classList.contains("item-qty") || target.classList.contains("item-ukd") || target.classList.contains("item-ufills")) {
                        // User changed quantity or unit price: re-enable auto-calculation
                        row.dataset.manualTotal = "false";
                    }
                }
                recalculate();
            } else {
                updatePreview();
            }
        });

        updateItemNumbers();
        recalculate();
    }

    function addItemRow(desc = "", qty = "", ukd = "", ufills = "", tkd = "", tfills = "") {
        const card = document.createElement("div");
        card.className = "item-card item-row";
        card.dataset.manualTotal = (tkd !== "" && (qty === "" || ukd === "")) ? "true" : "false";

        const nextIdx = (itemsContainer ? itemsContainer.querySelectorAll(".item-row").length : 0) + 1;

        card.innerHTML = `
            <div class="item-card-header">
                <span class="item-badge">Item <span class="item-index">${nextIdx}</span></span>
                <button type="button" class="btn btn-danger btn-sm remove-item-btn" title="Remove Item" style="padding: 0.35rem 0.75rem;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    <span>Delete</span>
                </button>
            </div>

            <div class="form-group" style="margin-bottom: 0.85rem;">
                <label class="form-label">Description &amp; Specifications</label>
                <textarea name="item_description[]" class="form-control calc-trigger item-desc" rows="2" placeholder="Item description / specifications" required>${desc}</textarea>
            </div>

            <div class="item-pricing-grid">
                <div class="form-group item-qty-wrap">
                    <label class="form-label">Quantity</label>
                    <input type="number" step="any" min="0" inputmode="decimal" name="item_quantity[]" class="form-control calc-trigger item-qty" value="${qty}" placeholder="Qty">
                </div>

                <div class="pricing-subgroup">
                    <label class="form-label">Price per piece (Individual)</label>
                    <div class="currency-split-inputs">
                        <div class="currency-col">
                            <span class="currency-tag">K.D</span>
                            <input type="number" min="0" inputmode="numeric" name="item_unit_kd[]" class="form-control calc-trigger item-ukd" value="${ukd}" placeholder="0">
                        </div>
                        <div class="currency-col">
                            <span class="currency-tag">Fills</span>
                            <input type="number" min="0" max="999" inputmode="numeric" name="item_unit_fills[]" class="form-control calc-trigger item-ufills" value="${ufills}" placeholder="0">
                        </div>
                    </div>
                </div>

                <div class="pricing-subgroup total-subgroup">
                    <div class="total-subgroup-header">
                        <label class="form-label" style="margin-bottom: 0;">Total price per piece</label>
                        <span class="calc-mode-indicator">Auto / Manual</span>
                    </div>
                    <div class="currency-split-inputs">
                        <div class="currency-col">
                            <span class="currency-tag">K.D</span>
                            <input type="number" min="0" inputmode="numeric" name="item_total_kd[]" class="form-control calc-trigger item-tkd" value="${tkd}" placeholder="0">
                        </div>
                        <div class="currency-col">
                            <span class="currency-tag">Fills</span>
                            <input type="number" min="0" max="999" inputmode="numeric" name="item_total_fills[]" class="form-control calc-trigger item-tfills" value="${tfills}" placeholder="0">
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (itemsContainer) {
            itemsContainer.appendChild(card);
            updateItemNumbers();
        }
    }

    function recalculate() {
        const rows = document.querySelectorAll(".item-row");
        let grandTotalKD = 0;
        let grandTotalFills = 0;

        rows.forEach((row) => {
            const qtyInput = row.querySelector(".item-qty");
            const ukdInput = row.querySelector(".item-ukd");
            const ufillsInput = row.querySelector(".item-ufills");
            const tkdInput = row.querySelector(".item-tkd");
            const tfillsInput = row.querySelector(".item-tfills");

            const isManual = row.dataset.manualTotal === "true";

            const qtyStr = (qtyInput?.value || "").trim();
            const ukdStr = (ukdInput?.value || "").trim();
            const ufillsStr = (ufillsInput?.value || "").trim();
            const tkdStr = (tkdInput?.value || "").trim();
            const tfillsStr = (tfillsInput?.value || "").trim();

            const qty = parseFloat(qtyStr);
            const ukd = parseInt(ukdStr, 10);
            const ufills = parseInt(ufillsStr, 10);

            const hasQty = !isNaN(qty) && qty > 0;
            const hasUnit = (!isNaN(ukd) && ukd > 0) || (!isNaN(ufills) && ufills > 0);

            let lineKD = 0;
            let lineFills = 0;

            if (!isManual && hasQty && hasUnit) {
                // Auto-calculation: Total price per piece = Quantity * Price per piece
                const unitTotal = (isNaN(ukd) ? 0 : ukd) + ((isNaN(ufills) ? 0 : ufills) / 1000.0);
                const lineTotal = qty * unitTotal;
                lineKD = Math.floor(lineTotal);
                lineFills = Math.round((lineTotal - lineKD) * 1000);
                tkdInput.value = lineKD > 0 ? lineKD : (lineFills > 0 ? 0 : "");
                tfillsInput.value = lineFills > 0 ? lineFills : "";
            } else {
                // Manual total price per piece (or when qty / price per piece are blank)
                const manualTKD = parseInt(tkdStr, 10);
                const manualTFills = parseInt(tfillsStr, 10);
                lineKD = !isNaN(manualTKD) ? manualTKD : 0;
                lineFills = !isNaN(manualTFills) ? manualTFills : 0;
            }

            grandTotalKD += lineKD;
            grandTotalFills += lineFills;
        });

        if (grandTotalFills >= 1000) {
            grandTotalKD += Math.floor(grandTotalFills / 1000);
            grandTotalFills = grandTotalFills % 1000;
        }

        const grandTotalDisplay = document.getElementById("grandTotalDisplay");
        if (grandTotalDisplay) {
            const fillsStr = grandTotalFills > 0 ? `.${String(grandTotalFills).padStart(3, '0')}` : '.000';
            grandTotalDisplay.textContent = `KD ${grandTotalKD}${fillsStr}`;
        }

        const wordsInput = document.getElementById("amount_in_words");
        if (wordsInput && !isCustomWordsEdited) {
            wordsInput.value = amountToWords(grandTotalKD, grandTotalFills);
        }

        updatePreview(grandTotalKD, grandTotalFills);
    }

    function updatePreview(grandTotalKD = null, grandTotalFills = null) {
        const companyName = document.getElementById("company_name")?.value || "WARDHAN TRADING EST.";
        const quotationNo = document.getElementById("quotation_no")?.value || "203/2020";
        const dateVal = document.getElementById("date")?.value || "24/9/2020";
        const customerName = document.getElementById("customer_name")?.value || "Radisson Blue Hotel, Kuwait";
        const inchargeVal = document.getElementById("incharge")?.value || "";
        const emailVal = document.getElementById("email")?.value || "thilakantmt@gmail.com";
        const phoneVal = document.getElementById("phone")?.value || "+965 99983543";
        const wordsVal = document.getElementById("amount_in_words")?.value || "KD Twenty Five";

        const pvCompany = document.getElementById("pvCompany");
        const pvQNo = document.getElementById("pvQNo");
        const pvDate = document.getElementById("pvDate");
        const pvCustomer = document.getElementById("pvCustomer");
        const pvWords = document.getElementById("pvWords");
        const pvIncharge = document.getElementById("pvIncharge");
        const pvEmail = document.getElementById("pvEmail");
        const pvPhone = document.getElementById("pvPhone");

        if (pvCompany) pvCompany.textContent = companyName;
        if (pvQNo) pvQNo.textContent = `Quotation No:${quotationNo}`;
        if (pvDate) pvDate.textContent = `Date  :  ${dateVal}`;
        if (pvCustomer) pvCustomer.textContent = customerName;
        if (pvWords) pvWords.textContent = wordsVal;
        if (pvIncharge) pvIncharge.textContent = inchargeVal ? `Incharge: ${inchargeVal}` : "Incharge:";
        if (pvEmail) {
            pvEmail.textContent = emailVal;
            pvEmail.href = `mailto:${emailVal}`;
        }
        if (pvPhone) pvPhone.textContent = `Ph no: ${phoneVal}`;

        // Populate table rows in paper preview
        const pvItemsBody = document.getElementById("pvItemsBody");
        if (pvItemsBody) {
            pvItemsBody.innerHTML = "";
            const rows = document.querySelectorAll(".item-row");
            let rowCount = 0;

            rows.forEach((row) => {
                const desc = row.querySelector(".item-desc")?.value || "";
                const qty = row.querySelector(".item-qty")?.value || "";
                const ukd = row.querySelector(".item-ukd")?.value || "";
                const ufills = row.querySelector(".item-ufills")?.value || "";
                const tkd = row.querySelector(".item-tkd")?.value || "";
                const tfills = row.querySelector(".item-tfills")?.value || "";

                if (desc.trim() || tkd || ukd || qty || tfills) {
                    rowCount++;
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td class="pv-cell-left">${escapeHtml(desc)}</td>
                        <td class="pv-cell-center">${qty}</td>
                        <td class="pv-cell-center">${ukd}</td>
                        <td class="pv-cell-center">${ufills}</td>
                        <td class="pv-cell-center">${tkd}</td>
                        <td class="pv-cell-center">${tfills}</td>
                    `;
                    pvItemsBody.appendChild(tr);
                }
            });

            // Minimum 8 padded rows
            const minRows = 8;
            for (let i = rowCount; i < minRows; i++) {
                const emptyTr = document.createElement("tr");
                emptyTr.innerHTML = `
                    <td class="pv-cell-left">&nbsp;</td>
                    <td class="pv-cell-center"></td>
                    <td class="pv-cell-center"></td>
                    <td class="pv-cell-center"></td>
                    <td class="pv-cell-center"></td>
                    <td class="pv-cell-center"></td>
                `;
                pvItemsBody.appendChild(emptyTr);
            }

            // Total row cells (properly separated)
            const pvTotKD = document.getElementById("pvTotKD");
            const pvTotFills = document.getElementById("pvTotFills");
            if (pvTotKD) pvTotKD.textContent = grandTotalKD !== null && grandTotalKD > 0 ? grandTotalKD : "";
            if (pvTotFills) pvTotFills.textContent = grandTotalFills !== null && grandTotalFills > 0 ? grandTotalFills : "";
        }
    }

    // Export globally for inline onclick handlers & reset actions
    window.addItemRow = addItemRow;
    window.recalculate = recalculate;
    window.updatePreview = updatePreview;

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/\n/g, "<br>");
    }
});
