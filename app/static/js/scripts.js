
document.addEventListener("DOMContentLoaded", function () {
   const openModalButton = document.getElementById("openModalButton");
   const closeModalButtons = document.querySelectorAll("#closeModalButton, #closeModalButtonBottom");
   const createUserModal = document.getElementById("createUserModal");

   openModalButton.addEventListener("click", function () {
      createUserModal.classList.remove("hidden");
      createUserModal.classList.add("flex");
   });

   closeModalButtons.forEach((button) => {
      button.addEventListener("click", function () {
         createUserModal.classList.add("hidden");
         createUserModal.classList.remove("flex");
      });
   });

   // window.addEventListener("click", function (event) {
   //    if (event.target == createUserModal) {
   //       createUserModal.classList.add("hidden");
   //    }
   // });
});
