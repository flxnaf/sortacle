// Initialize Lucide icons with customized stroke width
lucide.createIcons({
  attrs: {
    "stroke-width": 2.5,
  },
});

// Advanced Tab Navigation
const navItems = document.querySelectorAll(".nav-item[data-tab]");
const tabPanes = document.querySelectorAll(".tab-pane");
const titleElement = document.getElementById("current-tab-title");

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const tabId = item.getAttribute("data-tab");
    if (!tabId) return;

    // Toggle active nav
    navItems.forEach((nav) => nav.classList.remove("active"));
    item.classList.add("active");

    // Animate tab change
    tabPanes.forEach((pane) => {
      pane.style.opacity = "0";
      pane.style.transform = "translateY(10px)";

      setTimeout(() => {
        pane.classList.remove("active");
        if (pane.id === tabId) {
          pane.classList.add("active");
          setTimeout(() => {
            pane.style.opacity = "1";
            pane.style.transform = "translateY(0)";
          }, 50);
        }
      }, 300);
    });

    // Update header title
    const tabName = item.querySelector("span")?.textContent || "";
    titleElement.textContent = tabName === "Overview" ? "Project Overview" : tabName;
  });
});
