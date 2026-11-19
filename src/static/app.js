document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const participantsList = document.getElementById("participants-list");
  const navLinks = document.querySelectorAll(".main-nav a");
  const loginForm = document.getElementById("login-form");
  const loginEmail = document.getElementById("login-email");
  const loginPassword = document.getElementById("login-password");
  const authPanel = document.getElementById("auth-panel");
  const signedInPanel = document.getElementById("signed-in-panel");
  const signedInMessage = document.getElementById("signed-in-message");
  const logoutButton = document.getElementById("logout-button");
  const participantsNav = document.getElementById("participants-nav");
  const activitiesNav = document.getElementById("activities-nav");
  let authenticated = false;

  function showPage(pageName) {
    let validPage = ["home", "participants", "activities"].includes(pageName)
      ? pageName
      : "home";
    if (!authenticated && ["participants", "activities"].includes(validPage)) {
      validPage = "home";
      history.replaceState(null, "", "#home");
    }

    document.querySelectorAll(".page").forEach((page) => {
      const active = page.id === validPage;
      page.classList.toggle("active", active);
      page.classList.toggle("hidden", !active);
    });

    navLinks.forEach((link) => {
      const active = link.dataset.page === validPage;
      link.classList.toggle("active", active);
      if (active) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function setAuthenticated(email) {
    authenticated = Boolean(email);
    participantsNav.classList.toggle("hidden", !authenticated);
    activitiesNav.classList.toggle("hidden", !authenticated);
    authPanel.classList.toggle("hidden", authenticated);
    signedInPanel.classList.toggle("hidden", !authenticated);
    signedInMessage.textContent = authenticated ? `Signed in as ${email}` : "";

    if (!authenticated) {
      showPage("home");
      history.replaceState(null, "", "#home");
    }
  }

  async function checkSession() {
    try {
      const response = await fetch("/auth/session", { cache: "no-store" });
      const result = await response.json();
      setAuthenticated(result.authenticated ? result.email : null);
      if (authenticated) {
        await fetchActivityOptions();
        await fetchActivities();
      } else {
        await fetchActivityOptions();
      }
      showPage(window.location.hash.slice(1));
    } catch (error) {
      setAuthenticated(null);
      await fetchActivityOptions();
      console.error("Error checking sign-in session:", error);
    }
  }

  function renderParticipants(activities) {
    const memberships = new Map();

    Object.entries(activities).forEach(([activityName, details]) => {
      details.participants.forEach((participant) => {
        if (!memberships.has(participant)) {
          memberships.set(participant, []);
        }
        memberships.get(participant).push(activityName);
      });
    });

    participantsList.innerHTML = "";

    if (memberships.size === 0) {
      participantsList.innerHTML = '<p class="no-participants">No participants yet</p>';
      return;
    }

    [...memberships.entries()]
      .sort(([emailA], [emailB]) => emailA.localeCompare(emailB))
      .forEach(([participant, activityNames]) => {
        const card = document.createElement("div");
        card.className = "participant-card";

        const details = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = participant;
        const membership = document.createElement("p");
        membership.className = "participant-memberships";
        membership.textContent = `Activities: ${activityNames.join(", ")}`;
        details.append(name, membership);

        const actions = document.createElement("div");
        actions.className = "participant-actions";

        activityNames.forEach((activityName) => {
          const removeButton = document.createElement("button");
          removeButton.type = "button";
          removeButton.className = "remove-participant";
          removeButton.textContent = `Remove from ${activityName}`;
          removeButton.addEventListener("click", async () => {
            removeButton.disabled = true;
            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(participant)}`,
                { method: "DELETE" }
              );
              const result = await response.json();

              if (response.ok) {
                await fetchActivities();
                messageDiv.textContent = result.message;
                messageDiv.className = "success";
              } else {
                messageDiv.textContent = result.detail || "Failed to unregister participant";
                messageDiv.className = "error";
                removeButton.disabled = false;
              }
              messageDiv.classList.remove("hidden");
              setTimeout(() => messageDiv.classList.add("hidden"), 5000);
            } catch (error) {
              removeButton.disabled = false;
              messageDiv.textContent = "Failed to unregister participant.";
              messageDiv.className = "error";
              messageDiv.classList.remove("hidden");
              console.error("Error unregistering participant:", error);
            }
          });
          actions.appendChild(removeButton);
        });

        card.append(details, actions);
        participantsList.appendChild(card);
      });
  }

  async function fetchActivityOptions() {
    try {
      const response = await fetch("/activities/options", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load activity options");
      }
      const activityNames = await response.json();
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
      activityNames.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitySelect.innerHTML = '<option value="">Unable to load activities</option>';
      console.error("Error fetching activity options:", error);
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities", { cache: "no-store" });
      if (response.status === 401) {
        setAuthenticated(null);
        return;
      }
      if (!response.ok) {
        throw new Error("Failed to load activities");
      }
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      renderParticipants(activities);

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        const title = document.createElement("h4");
        title.textContent = name;

        const description = document.createElement("p");
        description.textContent = details.description;

        const schedule = document.createElement("p");
        schedule.innerHTML = "<strong>Schedule:</strong> ";
        schedule.append(document.createTextNode(details.schedule));

        const availability = document.createElement("p");
        availability.innerHTML = "<strong>Availability:</strong> ";
        availability.append(document.createTextNode(`${spotsLeft} spots left`));

        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";

        const participantsTitle = document.createElement("h5");
        participantsTitle.textContent = "Participants";

        const participantsList = document.createElement("ul");
        participantsList.className = "participants-list";

        if (details.participants.length === 0) {
          const emptyItem = document.createElement("li");
          emptyItem.className = "no-participants";
          emptyItem.textContent = "No participants yet";
          participantsList.appendChild(emptyItem);
        } else {
          details.participants.forEach((participant) => {
            const participantItem = document.createElement("li");
            participantItem.className = "participant-item";

            const participantName = document.createElement("span");
            participantName.className = "participant-name";
            participantName.textContent = participant;

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "delete-participant";
            deleteButton.setAttribute("aria-label", `Unregister ${participant}`);
            deleteButton.title = `Unregister ${participant}`;
            deleteButton.innerHTML = `
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 3h6l1 2h4v2H4V5h4l1-2zm-2 6h10l-.7 10.1A2 2 0 0 1 14.3 21H9.7a2 2 0 0 1-2-1.9L7 9zm3 2v7h2v-7h-2zm4 0v7h2v-7h-2z"/>
              </svg>
            `;
            deleteButton.addEventListener("click", async () => {
              deleteButton.disabled = true;
              try {
                const response = await fetch(
                  `/activities/${encodeURIComponent(name)}/signup?email=${encodeURIComponent(participant)}`,
                  { method: "DELETE" }
                );
                const result = await response.json();

                if (response.ok) {
                  await fetchActivities();
                  messageDiv.textContent = result.message;
                  messageDiv.className = "success";
                } else {
                  messageDiv.textContent = result.detail || "Failed to unregister participant";
                  messageDiv.className = "error";
                  deleteButton.disabled = false;
                }
                messageDiv.classList.remove("hidden");
                setTimeout(() => messageDiv.classList.add("hidden"), 5000);
              } catch (error) {
                deleteButton.disabled = false;
                messageDiv.textContent = "Failed to unregister participant.";
                messageDiv.className = "error";
                messageDiv.classList.remove("hidden");
                console.error("Error unregistering participant:", error);
              }
            });

            participantItem.append(participantName, deleteButton);
            participantsList.appendChild(participantItem);
          });
        }

        participantsSection.append(participantsTitle, participantsList);
        activityCard.append(
          title,
          description,
          schedule,
          availability,
          participantsSection
        );

        activitiesList.appendChild(activityCard);

      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        await fetchActivityOptions();
        if (authenticated) {
          await fetchActivities();
        }
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const response = await fetch(
        `/auth/login?email=${encodeURIComponent(loginEmail.value)}&password=${encodeURIComponent(loginPassword.value)}`,
        { method: "POST" }
      );
      const result = await response.json();
      if (response.ok) {
        loginForm.reset();
        setAuthenticated(result.email);
        await fetchActivities();
        showPage("activities");
        history.pushState(null, "", "#activities");
      } else {
        messageDiv.textContent = result.detail || "Sign-in failed";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
      }
    } catch (error) {
      messageDiv.textContent = "Sign-in failed.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing in:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      await fetch("/auth/logout", { method: "POST" });
      setAuthenticated(null);
      await fetchActivityOptions();
      showPage("home");
      history.pushState(null, "", "#home");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  });

  // Initialize app
  window.addEventListener("hashchange", () => {
    showPage(window.location.hash.slice(1));
  });
  checkSession();
});
