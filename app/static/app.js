// Configuration constants for Dynamic template forms
const TEMPLATE_SCHEMAS = {
    "welcome.html": [
        { label: "User Name", key: "name", type: "text", placeholder: "John Doe" },
        { label: "Company Name", key: "company", type: "text", placeholder: "Acme Corp" }
    ],
    "otp.html": [
        { label: "User Name", key: "name", type: "text", placeholder: "John Doe" },
        { label: "OTP Code", key: "otp", type: "text", placeholder: "123456" },
        { label: "Company Name", key: "company", type: "text", placeholder: "Acme Corp" }
    ],
    "invoice.html": [
        { label: "Client Name", key: "name", type: "text", placeholder: "John Doe" },
        { label: "Invoice Number", key: "invoice_number", type: "text", placeholder: "INV-2026-001" },
        { label: "Billing Date", key: "date", type: "date", placeholder: "" },
        { label: "Total Amount", key: "amount", type: "text", placeholder: "$249.00" },
        { label: "Company Name", key: "company", type: "text", placeholder: "Acme Corp" }
    ],
    "password_reset.html": [
        { label: "User Name", key: "name", type: "text", placeholder: "John Doe" },
        { label: "Reset Password Link", key: "reset_link", type: "url", placeholder: "https://acme.com/reset?token=xyz" },
        { label: "Company Name", key: "company", type: "text", placeholder: "Acme Corp" }
    ],
    "internship_certificate.html": [
        { label: "Intern Name", key: "name", type: "text", placeholder: "John Doe" },
        { label: "Internship Title", key: "internship_title", type: "text", placeholder: "Software Engineering Intern" },
        { label: "Date of Issue", key: "date", type: "text", placeholder: "July 4, 2026" },
        { label: "Company Name", key: "company", type: "text", placeholder: "Acme Corp" }
    ]
};

// State Variables
let attachedFile = null;
let htmlAttachedFile = null;
let bulkRecipientsFile = null;
let bulkAttachFile = null;
let logsCache = [];

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    setupTemplateFormBuilder();
    setupDragAndDrop();
    setupFormSubmissions();
    
    // Fetch dynamic template lists from backend
    fetchTemplates();
    
    // Load initial logs
    fetchLogs();
});

// 1. Sidebar tab switching navigation
function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".view-section");
    
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetSectionId = item.getAttribute("data-target");
            
            navItems.forEach(nav => nav.classList.remove("active"));
            sections.forEach(sec => sec.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(targetSectionId).classList.add("active");
            
            // If switched to logs section, refresh logs
            if (targetSectionId === "section-logs") {
                fetchLogs();
            }
        });
    });
}

// 2. Templates Management: Fetch and populate
async function fetchTemplates() {
    try {
        // Fetch single templates
        const singleResponse = await fetch("/api/templates");
        if (singleResponse.ok) {
            const singleData = await singleResponse.json();
            if (singleData.success) {
                populateTemplatesDropdown("html-template", singleData.templates);
            }
        }

        // Fetch bulk templates
        const bulkResponse = await fetch("/api/bulk-templates");
        if (bulkResponse.ok) {
            const bulkData = await bulkResponse.json();
            if (bulkData.success) {
                populateTemplatesDropdown("bulk-template", bulkData.templates, true);
            }
        }
    } catch (e) {
        console.error("Failed to load templates", e);
    }
}

function populateTemplatesDropdown(selectId, templates, isOptional = false) {
    const select = document.getElementById(selectId);
    
    // Clear existing
    if (isOptional) {
        select.innerHTML = '<option value="" selected>None - Send plain text body</option>';
    } else {
        select.innerHTML = '<option value="" disabled selected>Choose a template...</option>';
    }
    
    templates.forEach(tpl => {
        const opt = document.createElement("option");
        opt.value = tpl;
        opt.innerText = tpl;
        select.appendChild(opt);
    });
}

// 3. Dynamic template variables form builder
function setupTemplateFormBuilder() {
    // Helper to fetch and generate form fields dynamically for a select dropdown
    async function bindDropdownToFields(selectElement, variablesContainerElement, fieldsGridElement, apiPrefix, callbackOnTemplateChange) {
        selectElement.addEventListener("change", async (e) => {
            const selectedTemplate = e.target.value;
            fieldsGridElement.innerHTML = "";
            
            if (callbackOnTemplateChange) {
                callbackOnTemplateChange(selectedTemplate);
            }

            if (!selectedTemplate) {
                variablesContainerElement.classList.add("hidden");
                return;
            }
            
            // A. Check hardcoded schema (only for single templates preset)
            if (apiPrefix === "/api/templates") {
                const schema = TEMPLATE_SCHEMAS[selectedTemplate];
                if (schema && schema.length > 0) {
                    renderFields(schema, fieldsGridElement, variablesContainerElement);
                    return;
                }
            }
            
            // B. Fetch template content and extract dynamic variables
            try {
                const response = await fetch(`${apiPrefix}/${selectedTemplate}`);
                if (!response.ok) return;
                const data = await response.json();
                if (data.success && data.content) {
                    const regex = /\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g;
                    let match;
                    const variables = new Set();
                    while ((match = regex.exec(data.content)) !== null) {
                        variables.add(match[1].trim());
                    }
                    
                    if (variables.size > 0) {
                        const dynamicSchema = Array.from(variables).map(v => ({
                            label: v.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                            key: v,
                            type: "text",
                            placeholder: `Enter ${v}`
                        }));
                        renderFields(dynamicSchema, fieldsGridElement, variablesContainerElement);
                    } else {
                        variablesContainerElement.classList.add("hidden");
                    }
                }
            } catch (error) {
                console.error("Failed to parse custom variables", error);
                variablesContainerElement.classList.add("hidden");
            }
        });
    }

    function renderFields(fields, grid, container) {
        fields.forEach(field => {
            const group = document.createElement("div");
            group.className = "form-group";
            
            const label = document.createElement("label");
            label.innerText = field.label;
            label.setAttribute("for", `var-${field.key}`);
            
            const input = document.createElement("input");
            input.id = `var-${field.key}`;
            input.type = field.type;
            input.placeholder = field.placeholder || "";
            input.required = true;
            input.dataset.key = field.key;
            
            group.appendChild(label);
            group.appendChild(input);
            grid.appendChild(group);
        });
        container.classList.remove("hidden");
    }

    // Bind Instance 1: HTML Single Send Tab
    bindDropdownToFields(
        document.getElementById("html-template"),
        document.getElementById("template-variables-container"),
        document.getElementById("dynamic-fields-grid"),
        "/api/templates",
        null
    );

    // Bind Instance 2: Bulk Sender Tab
    const groupBulkBody = document.getElementById("group-bulk-body");
    const bulkBodyInput = document.getElementById("bulk-body");
    bindDropdownToFields(
        document.getElementById("bulk-template"),
        document.getElementById("bulk-variables-container"),
        document.getElementById("bulk-dynamic-fields-grid"),
        "/api/bulk-templates",
        (selectedTemplate) => {
            if (selectedTemplate) {
                // If HTML template is selected, hide the body textarea and set not-required
                groupBulkBody.classList.add("hidden");
                bulkBodyInput.required = false;
            } else {
                // Show body textarea
                groupBulkBody.classList.remove("hidden");
                bulkBodyInput.required = true;
            }
        }
    );
}

// 4. Drag & Drop Helper and Instances
function setupDragAndDrop() {
    function setupDragAndDropHelper(dropzoneId, fileInputId, fileInfoId, fileNameTextId, removeBtnId, onFileSelected, onFileCleared) {
        const dropzone = document.getElementById(dropzoneId);
        const fileInput = document.getElementById(fileInputId);
        const fileInfo = document.getElementById(fileInfoId);
        const fileNameText = document.getElementById(fileNameTextId);
        const removeBtn = document.getElementById(removeBtnId);
        const dropzoneText = dropzone.querySelector(".dropzone-text");
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.add("dragover");
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
            }, false);
        });
        
        dropzone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
        
        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
        
        removeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            clearFile();
        });
        
        function handleFileSelect(file) {
            onFileSelected(file);
            fileNameText.innerText = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
            fileInfo.classList.remove("hidden");
            dropzoneText.classList.add("hidden");
            fileInput.required = false;
        }
        
        function clearFile() {
            onFileCleared();
            fileInput.value = "";
            fileInfo.classList.add("hidden");
            dropzoneText.classList.remove("hidden");
        }
    }

    // Instance 1: Send with attachment file upload
    setupDragAndDropHelper(
        "dropzone", "attach-file", "file-info", "file-name-text", "remove-file-btn", 
        (file) => { attachedFile = file; }, 
        () => { 
            attachedFile = null; 
            document.getElementById("attach-file").required = true;
        }
    );

    // Instance 2: Templated email optional file upload
    setupDragAndDropHelper(
        "html-dropzone", "html-attach-file", "html-file-info", "html-file-name-text", "html-remove-file-btn", 
        (file) => { htmlAttachedFile = file; }, 
        () => { htmlAttachedFile = null; }
    );

    // Instance 3: Bulk recipients CSV/TXT file upload
    setupDragAndDropHelper(
        "bulk-recipients-dropzone", "bulk-recipients-file", "bulk-recipients-file-info", "bulk-recipients-file-name-text", "bulk-recipients-remove-file-btn", 
        (file) => { bulkRecipientsFile = file; }, 
        () => { bulkRecipientsFile = null; }
    );

    // Instance 4: Bulk attachments file upload
    setupDragAndDropHelper(
        "bulk-attach-dropzone", "bulk-attach-file", "bulk-attach-file-info", "bulk-attach-file-name-text", "bulk-attach-remove-file-btn", 
        (file) => { bulkAttachFile = file; }, 
        () => { bulkAttachFile = null; }
    );
}

// 5. Form Submissions
function setupFormSubmissions() {
    // A. Send Plain Email
    const formPlain = document.getElementById("form-plain");
    formPlain.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const payload = {
            recipient: document.getElementById("plain-recipient").value,
            subject: document.getElementById("plain-subject").value,
            body: document.getElementById("plain-body").value
        };
        
        await submitEmail("/send-email", payload, "submit-plain", () => {
            formPlain.reset();
        });
    });
    
    // B. Send HTML Template Email
    const formHtml = document.getElementById("form-html");
    formHtml.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const recipient = document.getElementById("html-recipient").value;
        const subject = document.getElementById("html-subject").value;
        const templateName = document.getElementById("html-template").value;
        const dynamicInputs = document.querySelectorAll("#dynamic-fields-grid input");
        const templateData = {};
        
        dynamicInputs.forEach(input => {
            templateData[input.dataset.key] = input.value;
        });

        const submitBtn = document.getElementById("submit-html");
        setLoadingState(submitBtn, true);

        if (htmlAttachedFile) {
            const formData = new FormData();
            formData.append("recipient", recipient);
            formData.append("subject", subject);
            formData.append("template_name", templateName);
            formData.append("template_data_json", JSON.stringify(templateData));
            formData.append("file", htmlAttachedFile);

            try {
                const response = await fetch("/send-html-email-with-attachment", {
                    method: "POST",
                    body: formData
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    showAlert("Templated HTML email with file attachment sent successfully!", "success");
                    formHtml.reset();
                    document.getElementById("html-remove-file-btn").click();
                    document.getElementById("template-variables-container").classList.add("hidden");
                    document.getElementById("dynamic-fields-grid").innerHTML = "";
                } else {
                    showAlert(result.message || "Failed to send templated email with attachment.", "error");
                }
            } catch (error) {
                showAlert(`Connection error: ${error.message}`, "error");
            } finally {
                setLoadingState(submitBtn, false);
                fetchLogs();
            }
        } else {
            const payload = {
                recipient: recipient,
                subject: subject,
                template_name: templateName,
                template_data: templateData
            };
            
            await submitEmail("/send-html-email", payload, "submit-html", () => {
                formHtml.reset();
                document.getElementById("template-variables-container").classList.add("hidden");
                document.getElementById("dynamic-fields-grid").innerHTML = "";
            });
        }
    });
    
    // C. Send Email with Attachment
    const formAttachment = document.getElementById("form-attachment");
    formAttachment.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const recipient = document.getElementById("attach-recipient").value;
        const subject = document.getElementById("attach-subject").value;
        const body = document.getElementById("attach-body").value;
        
        if (!attachedFile) {
            showAlert("Please upload or drag a file to attach.", "error");
            return;
        }
        
        const formData = new FormData();
        formData.append("recipient", recipient);
        formData.append("subject", subject);
        formData.append("body", body);
        formData.append("file", attachedFile);
        
        const submitBtn = document.getElementById("submit-attachment");
        setLoadingState(submitBtn, true);
        
        try {
            const response = await fetch("/send-email-with-attachment", {
                method: "POST",
                body: formData
            });
            const result = await response.json();
            
            if (response.ok && result.success) {
                showAlert("Email with file attachment sent successfully!", "success");
                formAttachment.reset();
                document.getElementById("remove-file-btn").click();
            } else {
                showAlert(result.message || "Failed to send email with attachment.", "error");
            }
        } catch (error) {
            showAlert(`Connection error: ${error.message}`, "error");
        } finally {
            setLoadingState(submitBtn, false);
            fetchLogs();
        }
    });

    // D. Custom HTML Template Builder
    const formBuilder = document.getElementById("form-builder");
    formBuilder.addEventListener("submit", async (e) => {
        e.preventDefault();

        const name = document.getElementById("builder-name").value.trim();
        const scope = document.getElementById("builder-scope").value;
        const content = document.getElementById("builder-content").value;

        if (!name.endsWith(".html")) {
            showAlert("Template file name must end with .html", "error");
            return;
        }

        const payload = { name, content };
        const submitBtn = document.getElementById("submit-builder");
        setLoadingState(submitBtn, true);

        // Determine destination endpoint based on selected Scope
        const endpointUrl = scope === "bulk" ? "/api/bulk-templates" : "/api/templates";

        try {
            const response = await fetch(endpointUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (response.ok && result.success) {
                showAlert(result.message || "Custom template saved successfully!", "success");
                formBuilder.reset();
                await fetchTemplates();
            } else {
                showAlert(result.message || "Failed to save custom template.", "error");
            }
        } catch (error) {
            showAlert(`Connection error: ${error.message}`, "error");
        } finally {
            setLoadingState(submitBtn, false);
        }
    });

    // E. Bulk Email Sender Submission
    const formBulk = document.getElementById("form-bulk");
    formBulk.addEventListener("submit", async (e) => {
        e.preventDefault();

        const recipients = document.getElementById("bulk-recipients").value;
        const subject = document.getElementById("bulk-subject").value;
        const templateName = document.getElementById("bulk-template").value;
        const body = document.getElementById("bulk-body").value;

        if (!recipients && !bulkRecipientsFile) {
            showAlert("Please enter a comma-separated recipients list or upload a recipients list file.", "error");
            return;
        }

        const formData = new FormData();
        if (recipients) formData.append("recipients", recipients);
        if (bulkRecipientsFile) formData.append("recipients_file", bulkRecipientsFile);
        formData.append("subject", subject);

        if (templateName) {
            // Append template configuration
            formData.append("template_name", templateName);
            const dynamicInputs = document.querySelectorAll("#bulk-dynamic-fields-grid input");
            const templateData = {};
            dynamicInputs.forEach(input => {
                templateData[input.dataset.key] = input.value;
            });
            formData.append("template_data_json", JSON.stringify(templateData));
        } else {
            // Send standard body
            formData.append("body", body);
        }

        // Optional bulk attachment file
        if (bulkAttachFile) {
            formData.append("file", bulkAttachFile);
        }

        const submitBtn = document.getElementById("submit-bulk");
        setLoadingState(submitBtn, true);

        try {
            const response = await fetch("/send-bulk-email", {
                method: "POST",
                body: formData
            });
            const result = await response.json();

            if (response.ok && result.success) {
                showAlert(result.message || "Bulk sending scheduled in background successfully!", "success");
                formBulk.reset();
                
                // Reset dropzones
                if (bulkRecipientsFile) document.getElementById("bulk-recipients-remove-file-btn").click();
                if (bulkAttachFile) document.getElementById("bulk-attach-remove-file-btn").click();
                
                // Hide dynamic template grids
                document.getElementById("bulk-variables-container").classList.add("hidden");
                document.getElementById("bulk-dynamic-fields-grid").innerHTML = "";
                document.getElementById("group-bulk-body").classList.remove("hidden");
                document.getElementById("bulk-body").required = false; // reset
            } else {
                showAlert(result.message || "Failed to schedule bulk email sending.", "error");
            }
        } catch (error) {
            showAlert(`Connection error: ${error.message}`, "error");
        } finally {
            setLoadingState(submitBtn, false);
            
            // Delay refresh logs briefly so background tasks can start writing database inserts
            setTimeout(fetchLogs, 1500);
        }
    });
    
    // Log refresh button
    document.getElementById("btn-refresh-logs").addEventListener("click", fetchLogs);
}

// 6. Submit Utilities
async function submitEmail(url, payload, buttonId, successCallback) {
    const submitBtn = document.getElementById(buttonId);
    setLoadingState(submitBtn, true);
    
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showAlert(result.message || "Email delivered successfully!", "success");
            if (successCallback) successCallback();
        } else {
            showAlert(result.message || "Failed to deliver email.", "error");
        }
    } catch (error) {
        showAlert(`Connection error: ${error.message}`, "error");
    } finally {
        setLoadingState(submitBtn, false);
        fetchLogs();
    }
}

function setLoadingState(button, isLoading) {
    const textNode = button.querySelector(".btn-text");
    const spinner = button.querySelector(".spinner");
    
    if (isLoading) {
        button.disabled = true;
        textNode.classList.add("hidden");
        spinner.classList.remove("hidden");
    } else {
        button.disabled = false;
        textNode.classList.remove("hidden");
        spinner.classList.add("hidden");
    }
}

// 7. Alert System
function showAlert(message, type) {
    const banner = document.getElementById("alert-banner");
    const textSpan = banner.querySelector(".alert-message");
    
    banner.className = `alert ${type}`;
    textSpan.innerText = message;
    
    setTimeout(() => {
        closeAlert();
    }, 8000);
}

function closeAlert() {
    const banner = document.getElementById("alert-banner");
    banner.classList.add("hidden");
}

// 8. Log and statistics rendering
async function fetchLogs() {
    try {
        const response = await fetch("/api/logs");
        if (!response.ok) return;
        
        const data = await response.json();
        if (data.success) {
            logsCache = data.logs;
            renderLogsTable(data.logs);
            updateDashboardStats(data.logs);
        }
    } catch (e) {
        console.error("Failed to fetch logs", e);
    }
}

function renderLogsTable(logs) {
    const tbody = document.getElementById("logs-tbody");
    tbody.innerHTML = "";
    
    if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="no-logs">No transaction history found. Logs will appear after you send emails.</td></tr>`;
        return;
    }
    
    logs.forEach(log => {
        const tr = document.createElement("tr");
        
        tr.addEventListener("click", () => {
            openDetailModal(log.id);
        });
        
        const statusTd = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = `status-badge ${log.status.toLowerCase()}`;
        badge.innerText = log.status;
        statusTd.appendChild(badge);
        
        const timeTd = document.createElement("td");
        timeTd.innerText = log.timestamp || "N/A";
        
        const recTd = document.createElement("td");
        recTd.innerText = log.recipient || "N/A";
        
        const detailsTd = document.createElement("td");
        if (log.status === "SUCCESS") {
            detailsTd.innerHTML = `<strong>Subject:</strong> ${log.subject || "N/A"}`;
        } else {
            const errMsg = log.error_message || "Unknown error";
            detailsTd.innerHTML = `<span style="color:#ef4444;"><strong>Failed:</strong> ${errMsg.substring(0, 50)}${errMsg.length > 50 ? '...' : ''}</span>`;
        }
        
        const provTd = document.createElement("td");
        provTd.innerText = log.provider || "SMTP";
        
        const speedTd = document.createElement("td");
        speedTd.innerText = log.response_time ? `${log.response_time.toFixed(3)} sec` : "-";
        
        tr.appendChild(statusTd);
        tr.appendChild(timeTd);
        tr.appendChild(recTd);
        tr.appendChild(detailsTd);
        tr.appendChild(provTd);
        tr.appendChild(speedTd);
        
        tbody.appendChild(tr);
    });
}

function updateDashboardStats(logs) {
    const totalElement = document.getElementById("stat-total");
    const rateElement = document.getElementById("stat-rate");
    
    const totalCount = logs.length;
    if (totalCount === 0) {
        totalElement.innerText = "0";
        rateElement.innerText = "0%";
        return;
    }
    
    const successCount = logs.filter(l => l.status === "SUCCESS").length;
    const successRate = Math.round((successCount / totalCount) * 100);
    
    totalElement.innerText = totalCount;
    rateElement.innerText = `${successRate}%`;
}

// 9. Modal Management
function openDetailModal(logId) {
    const log = logsCache.find(l => l.id === logId);
    if (!log) return;
    
    const modal = document.getElementById("detail-modal");
    
    const statusSpan = document.getElementById("detail-status");
    statusSpan.className = `status-badge ${log.status.toLowerCase()}`;
    statusSpan.innerText = log.status;
    
    document.getElementById("detail-timestamp").innerText = log.timestamp || "N/A";
    document.getElementById("detail-recipient").innerText = log.recipient || "N/A";
    document.getElementById("detail-subject").innerText = log.subject || "N/A";
    document.getElementById("detail-provider").innerText = log.provider || "SMTP";
    document.getElementById("detail-time").innerText = log.response_time ? `${log.response_time.toFixed(3)} sec` : "N/A";
    
    const groupTemplate = document.getElementById("group-template");
    const detailTemplate = document.getElementById("detail-template");
    if (log.template_name) {
        let varsText = "";
        try {
            const parsedVars = JSON.parse(log.template_data);
            varsText = Object.entries(parsedVars).map(([k, v]) => `${k}: "${v}"`).join(", ");
        } catch (e) {
            varsText = log.template_data || "";
        }
        detailTemplate.innerHTML = `<strong>Template:</strong> ${log.template_name}<br><strong>Variables:</strong> { ${varsText} }`;
        groupTemplate.classList.remove("hidden");
    } else {
        groupTemplate.classList.add("hidden");
    }
    
    const groupAttachment = document.getElementById("group-attachment");
    const detailAttachment = document.getElementById("detail-attachment");
    if (log.attachment_name) {
        detailAttachment.innerText = log.attachment_name;
        groupAttachment.classList.remove("hidden");
    } else {
        groupAttachment.classList.add("hidden");
    }
    
    const groupError = document.getElementById("group-error");
    const detailError = document.getElementById("detail-error");
    if (log.status === "FAILED") {
        detailError.innerText = log.error_message || "Unknown error details";
        groupError.classList.remove("hidden");
    } else {
        groupError.classList.add("hidden");
    }
    
    const previewIframe = document.getElementById("detail-preview");
    if (log.body) {
        previewIframe.srcdoc = log.body;
    } else {
        previewIframe.srcdoc = `<div style="font-family:sans-serif;color:#64748b;padding:20px;text-align:center;">No message body content available.</div>`;
    }
    
    modal.classList.remove("hidden");
    
    const closeBtn = document.getElementById("modal-close-btn");
    const closeModal = () => {
        modal.classList.add("hidden");
        previewIframe.srcdoc = "";
        closeBtn.removeEventListener("click", closeModal);
        modal.removeEventListener("click", onOverlayClick);
        document.removeEventListener("keydown", onEscPress);
    };
    
    const onOverlayClick = (e) => {
        if (e.target === modal) {
            closeModal();
        }
    };
    
    const onEscPress = (e) => {
        if (e.key === "Escape") {
            closeModal();
        }
    };
    
    closeBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", onOverlayClick);
    document.addEventListener("keydown", onEscPress);
}
