// Function to open the modal
function openModal(modalId) {
   var modal = document.getElementById(modalId);
   if (modal) {
      modal.style.display = 'flex'; 
   } else {
      console.error('Modal element not found.');
   }
}

// Function to close the modal
function closeModal(modalId) {
   var modal = document.getElementById(modalId);
   if (modal) {
      modal.style.display = 'none'; 
   } else {
      console.error('Modal element not found.');
   }
}

// Close flash message
function closeFlashMessage(button) {
   var flashMessage = button.parentElement;
   flashMessage.style.display = "none";
}