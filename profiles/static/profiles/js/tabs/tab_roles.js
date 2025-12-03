

function renderTabRolesInit() {
    const initHtml = /*html*/`
        <h1 class="bold-main mt-1 mb-2 font-xxl">Lista de Usuarios</h1>

        <form class="d-flex-col-row justify-center align-center gap-2 mt-1 mb-3" id="form-user-table-tab">
            <strong class="bold-main">Filtrar por Email:</strong>

            <div class="cont-user-search">
                <input type="search" name="search" placeholder="Buscar usuario...">
                <button class="btn" type="submit">
                    <i class="ri-user-search-line font-lg search-icon"></i>
                </button>
            </div>

            <select class="w-min select-users-role" name="role"> </select>
        </form>

        <div class="cont-table-user border-bot-second">
            <strong class="d-desktop-flex">Nombre</strong>
            <strong class="d-desktop-flex">Apellido</strong>
            <strong>Email</strong>
            <strong>Rol</strong>
            <span></span>
        </div>

        <div class="cont-forms-users"> </div>
    `.trim();

    // Create a temporary container element and insert the HTML string
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = initHtml;

    // Retrieve references to key containers for later dynamic insertion
    const selectUsers = tempDiv.querySelector('.select-users-role');
    const contFormsRole = tempDiv.querySelector('.cont-forms-users');

    // Move the created elements into a DocumentFragment for efficient DOM insertion
    const fragment = document.createDocumentFragment();
    while (tempDiv.firstChild) {
        fragment.appendChild(tempDiv.firstChild);
    }
    
    // Return the fragment and container references for further use
    return { htmlToAppend: fragment, selectUsers, contFormsRole };
}


/**
 * Renders a set of <option> elements for a <select> dropdown based on a roles object.
 * 
 * The function generates the HTML string for the options, marking the option matching
 * the current choice as selected. It can either return the HTML string or directly
 * insert it into a given container element.
 * 
 * @param {HTMLElement} container - The DOM element (usually a <select>) where the options will be inserted.
 * @param {Object} roles - An object where keys are role identifiers and values are role display names.
 *                         Example: { "admin": "Admin", "seller": "Seller", "buyer": "Buyer" }
 * @param {string} choice - The currently selected role key, which will be marked with the `selected` attribute.
 * @param {boolean} [onlyHtml=false] - If true, the function returns the generated HTML string without inserting it into the container.
 *                                     If false (default), the function sets the container's innerHTML to the generated options.
 * 
 * @returns {string|undefined} - Returns the HTML string if `onlyHtml` is true; otherwise, returns undefined.
 */
function renderRolesSelect(container, roles, choice, onlyHtml = false) {
    const optionsHtml = Object.entries(roles).map(([key, value]) => {
        return /*html*/`
            <option value="${key}" ${key === choice ? 'selected' : ''}>${value}es</option>
        `;
    }).join('');

    if (onlyHtml) return optionsHtml;
    container.innerHTML = optionsHtml;
}


/**
 * Renders a table of users with editable role selection inside a given container.
 * 
 * For each user, this function creates a form containing the user's first name, last name,
 * email, a <select> dropdown for role selection (using `renderRolesSelect` to generate options),
 * and a submit button labeled "Editar".
 * 
 * Note: The inner text inside the HTML (e.g., button label "Editar") is kept as-is and not translated.
 * 
 * @param {HTMLElement} container - The DOM element where the user forms will be inserted.
 * @param {Array<Object>} users - Array of user objects. Each user object is expected to have:
 *                                - first_name
 *                                - last_name
 *                                - email
 *                                - role (key matching roles object)
 *                                - id (used for data-index attribute)
 * @param {Object} roles - An object mapping role keys to display names, used to generate the <select> options.
 *                         Example: { "admin": "Admin", "seller": "Vendedor", "buyer": "Comprador" }
 */
function renderRolesUsersTable(container, users, roles) {
    const rowUsers = users.map(u => {
        const user = deepEscape(u);

        return /*html*/`
            <form class="cont-table-user border-bot-second form-user-role" data-index="${user.id}">
                <span class="d-desktop-flex">${user.first_name}</span>
                <span class="d-desktop-flex">${user.last_name}</span>

                <strong>${user.email}</strong>

                <select name="role">
                    ${renderRolesSelect(container, roles, user.role, true)}
                </select>

                <button class="btn btn-32 w-100 gap-1 btn-alt" type="submit"> 
                    <i class="ri-edit-box-line font-lg d-desktop-flex"></i>
                    <strong>Editar</strong>
                </button>
            </form>
        `;
    }).join('');
    container.innerHTML = rowUsers;
}


/**
 * Creates and renders the "Roles" tab content inside a given container.
 *
 * This function initializes the tab only once by generating the base HTML structure
 * and rendering the roles select dropdown and the user role forms. On subsequent calls,
 * it updates only the relevant inner elements without re-creating the entire structure.
 *
 * @param {HTMLElement} container - The DOM element where the roles tab content will be rendered.
 * @param {Object} data - The data object containing:
 *   - choices: Object mapping role keys to display names (e.g., { admin: "Admin", buyer: "Comprador" }).
 *   - choice: The currently selected role key (string).
 *   - users: Array of user objects with at least `id`, `first_name`, `last_name`, `email`, and `role`.
 */
function createTabRoles(container, data) {
    if (!container._hasInit) {
        // Generate base HTML structure and retrieve relevant sub-containers
        const { htmlToAppend, selectUsers, contFormsRole } = renderTabRolesInit();

        renderRolesSelect(selectUsers, data.choices, data.choice);
        renderRolesUsersTable(contFormsRole, data.users, data.choices);

        // Append the generated fragment to the container
        container.appendChild(htmlToAppend);
        container._hasInit = true;
        return;
    }

    // On subsequent calls, update only the forms inside the existing container
    const selectUsers = container.querySelector('.select-users-role');
    const contFormsRole = container.querySelector('.cont-forms-users');
    renderRolesSelect(selectUsers, data.choices, data.choice);
    renderRolesUsersTable(contFormsRole, data.users, data.choices);
}
