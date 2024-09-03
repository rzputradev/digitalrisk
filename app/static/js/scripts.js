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
      modal.classList.toggle('flex'); 
      modal.classList.toggle('hidden'); 
   } else {
      console.error('Modal element not found.');
   }
}

// Close flash message
function closeFlashMessage(button) {
   var flashMessage = button.parentElement;
   flashMessage.style.display = "none";
}

function commaSeparation(input) {
   let value = input.value.replace(/[^0-9]/g, "");
   if (value === "") return;

   let integerPart = value.slice(0, -2) || "0";
   let decimalPart = value.slice(-2).padStart(2, "0"); 

   let formattedIntegerPart = new Intl.NumberFormat("en-US", { minimumFractionDigits: 0 }).format(integerPart);

   input.value = formattedIntegerPart + "." + decimalPart;
}




document.addEventListener('DOMContentLoaded', function () {
   const flashContainer = document.getElementById('flash-messages');

   if (flashContainer) {
      const flashMessages = flashContainer.querySelectorAll('.flash-message');

      flashMessages.forEach(function (message, index) {
         setTimeout(function () {
            message.classList.add('show');
         }, 100 * index); // Staggered delay for each message

         // Add event listener to close button
         const closeButton = message.querySelector('.close-toast');
         closeButton.addEventListener('click', function () {
            closeToast(message);
         });
      });

      flashMessages.forEach(function (message) {
         setTimeout(function () {
            closeToast(message);
         }, 5000); // Adjust removal time as needed
      });
   }

   function closeToast(message) {
      message.classList.remove('show');
      setTimeout(function () {
         message.remove();
      }, 600); // Match this with the transition duration
   }
});