document.addEventListener("DOMContentLoaded", () => {
	const todayButton = document.querySelector("[data-set-today]");
	const startDateInput = document.querySelector("#start_date");
	const endDateInput = document.querySelector("#end_date");

	if (!todayButton || !startDateInput || !endDateInput) {
		return;
	}

	todayButton.addEventListener("click", () => {
		const today = new Date().toISOString().split("T")[0];
		startDateInput.value = today;
		endDateInput.value = today;
	});
});
