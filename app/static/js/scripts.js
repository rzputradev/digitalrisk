// Function to open the modal
function openModal(modalId) {
   var modal = document.getElementById(modalId);
   if (modal) {
      modal.classList.toggle('flex'); // Add or remove the 'flex' class
      modal.classList.toggle('hidden'); // Add or remove the 'hidden' class
   } else {
      console.error('Modal element not found.');
   }
}

function closeModal(modalId) {
   var modal = document.getElementById(modalId);
   if (modal) {
      modal.classList.toggle('flex'); // Add or remove the 'flex' class
      modal.classList.toggle('hidden'); // Add or remove the 'hidden' class
   } else {
      console.error('Modal element not found.');
   }
}

// Close flash message
function closeFlashMessage(button) {
   var flashMessage = button.parentElement;
   flashMessage.style.display = "none";
}