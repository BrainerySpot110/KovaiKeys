const BASE_URL = "";

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;



function initInteractiveBackground() {


    if (!document.getElementById("bg-image")) {
        const img = document.createElement("div");
        img.id = "bg-image";
        document.body.prepend(img);
    }

    if (prefersReducedMotion) {
        return;
    }

    if (!document.getElementById("bg-grid")) {
        const grid = document.createElement("div");
        grid.id = "bg-grid";
        document.body.prepend(grid);
    }

    let targetX = 50, targetY = 20, currentX = 50, currentY = 20;

    window.addEventListener("pointermove", (e) => {
        targetX = (e.clientX / window.innerWidth) * 100;
        targetY = (e.clientY / window.innerHeight) * 100;
    });

    function animateSpotlight() {
        currentX += (targetX - currentX) * 0.08;
        currentY += (targetY - currentY) * 0.08;
        document.documentElement.style.setProperty("--mx", currentX + "%");
        document.documentElement.style.setProperty("--my", currentY + "%");
        requestAnimationFrame(animateSpotlight);
    }

    requestAnimationFrame(animateSpotlight);


    const house = document.querySelector(".blueprint-house");

    if (house) {
        window.addEventListener("pointermove", (e) => {
            const dx = (e.clientX / window.innerWidth - 0.5) * 10;
            const dy = (e.clientY / window.innerHeight - 0.5) * 10;
            house.style.transform = `translate(${dx}px, ${dy}px)`;
        });
    }
    document.querySelectorAll(".spec-card, .detail-card").forEach((card) => {

        card.style.transformStyle = "preserve-3d";

        card.addEventListener("pointermove", (e) => {
            const rect = card.getBoundingClientRect();
            const px = (e.clientX - rect.left) / rect.width - 0.5;
            const py = (e.clientY - rect.top) / rect.height - 0.5;
            card.style.transform =
                `perspective(700px) rotateX(${(-py * 6).toFixed(2)}deg) rotateY(${(px * 6).toFixed(2)}deg) translateY(-4px)`;
        });

        card.addEventListener("pointerleave", () => {
            card.style.transform = "";
        });
    });
}



function showToast(text, type = "") {

    const stack = document.getElementById("toast-stack");

    if (!stack) {
       
        alert(text);
        return;
    }

    const toast = document.createElement("div");
    toast.className = "toast" + (type ? ` toast--${type}` : "");
    toast.textContent = text;

    stack.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = "opacity 0.3s ease";
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}




async function login() {

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (email === "" || password === "") {

        document.getElementById("message").innerHTML =
            "Please fill all fields";

        return;
    }

    const response = await fetch(BASE_URL + "/login", {

        method: "POST",

        credentials: "include",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            email: email,
            password: password
        })

    });

    const result = await response.json();

    if (response.ok) {

        localStorage.setItem("user", JSON.stringify(result));

        showToast(`Welcome back, ${result.name}!`, "success");

        setTimeout(() => {
            window.location.href = "/";
        }, 500);

    } else {

        document.getElementById("message").innerHTML =
            result.detail;
    }

}


async function register() {

    const selectedRole = document.querySelector('input[name="role"]:checked');

    const user = {

        name: document.getElementById("name").value,

        email: document.getElementById("email").value,

        password: document.getElementById("password").value,

        role: selectedRole ? selectedRole.value : "Buyer"

    };

    if (
        user.name === "" ||
        user.email === "" ||
        user.password === ""
    ) {

        document.getElementById("message").innerHTML =
            "Please fill all fields";

        return;
    }

    const response = await fetch(BASE_URL + "/register", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(user)

    });

    const result = await response.json();

    if (response.ok) {

        showToast("Registration successful — log in to continue.", "success");

        setTimeout(() => {
            window.location.href = "/login-page";
        }, 600);

    } else {

        document.getElementById("message").innerHTML =
            result.detail;

    }

}


async function logout() {

    await fetch(BASE_URL + "/logout", {
        method: "POST",
        credentials: "include"
    });

    localStorage.removeItem("user");

    showToast("Logged out", "");

    setTimeout(() => {
        window.location.href = "/";
    }, 300);

}



async function renderRoleNav() {

    const nav = document.getElementById("role-nav");

    if (!nav) {
        return;
    }

    const response = await fetch(BASE_URL + "/me", {
        credentials: "include"
    });

    const me = await response.json();

    let html = "";

    if (me.logged_in) {

        html += `<p>Signed in as <strong>${me.name}</strong> · ${me.role}</p>`;

        if (me.can_manage_properties) {
            html += `<a href="/add-property-page" class="btn btn--ghost btn--sm">+ Add Property</a>`;
        }

        if (me.can_view_users) {
            html += `<a href="#" class="btn btn--ghost btn--sm" onclick="loadUsers(); return false;">Manage Users</a>`;
        }

        html += `<button class="btn--sm" onclick="logout()">Logout</button>`;

    } else {

        html += `<a href="/login-page" class="btn btn--ghost btn--sm">Login</a>`;
        html += `<a href="/register-page" class="btn btn--sm">Register</a>`;
    }

    nav.innerHTML = html;
}


async function loadUsers() {

    const response = await fetch(BASE_URL + "/users", {
        credentials: "include"
    });

    if (!response.ok) {
        showToast("You don't have permission to view users.", "error");
        return;
    }

    const users = await response.json();

    const list = users
        .map(u => `${u.name} — ${u.email} (${u.role})`)
        .join("\n");

    alert("Registered Users:\n\n" + list);
}



const imageInput = document.getElementById("image");

if (imageInput) {

    const dropzone = imageInput.closest(".upload-drop");

    imageInput.addEventListener("change", function () {

        const file = this.files[0];

        if (file) {

            const reader = new FileReader();

            reader.onload = function (e) {

                const preview = document.getElementById("preview");

                if (preview) {

                    preview.src = e.target.result;

                    preview.style.display = "block";

                }

            };

            reader.readAsDataURL(file);

        }

    });

    if (dropzone) {

        ["dragover", "dragleave", "drop"].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => e.preventDefault());
        });

        dropzone.addEventListener("dragover", () => {
            dropzone.style.borderColor = "var(--brass-500)";
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.style.borderColor = "";
        });

        dropzone.addEventListener("drop", (e) => {

            dropzone.style.borderColor = "";

            const file = e.dataTransfer.files[0];

            if (file) {
                imageInput.files = e.dataTransfer.files;
                imageInput.dispatchEvent(new Event("change"));
            }

        });
    }

}


function callBroker(number) {

    window.location.href = "tel:" + number;

}


function viewProperty(id) {

    window.location.href = "/properties/" + id;

}


async function markSold(id, propertyType, onDetailPage) {

    const response = await fetch(BASE_URL + `/properties/${id}/mark-sold`, {
        method: "POST",
        credentials: "include"
    });

    const result = await response.json();

    if (!response.ok) {
        showToast(result.detail || "Couldn't update that listing.", "error");
        return;
    }

    showToast(result.message, "success");

    setTimeout(() => window.location.reload(), 500);
}


async function deleteProperty(id, onDetailPage) {

    const sure = confirm("Delete this listing permanently? This can't be undone.");

    if (!sure) {
        return;
    }

    const response = await fetch(BASE_URL + `/properties/${id}`, {
        method: "DELETE",
        credentials: "include"
    });

    const result = await response.json();

    if (!response.ok) {
        showToast(result.detail || "Couldn't delete that listing.", "error");
        return;
    }

    showToast("Property deleted", "success");

    if (onDetailPage) {
        setTimeout(() => { window.location.href = "/property-page"; }, 500);
    } else {
        const card = document.getElementById(`card-${id}`);
        if (card) {
            card.style.transition = "opacity 0.3s ease, transform 0.3s ease";
            card.style.opacity = "0";
            card.style.transform = "scale(0.94)";
            setTimeout(() => card.remove(), 300);
        }
    }
}


document.addEventListener("DOMContentLoaded", () => {
    renderRoleNav();
    initInteractiveBackground();
});
