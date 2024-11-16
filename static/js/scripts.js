document.addEventListener('DOMContentLoaded', function() {
   


    // // Login form submission
    // document.getElementById('loginForm').addEventListener('submit', function(event) {
    //     event.preventDefault();
    
    //     const email = document.getElementById('email').value;
    //     const password = document.getElementById('password').value;
    
    //     // Ensure email and password are not empty
    //     if (!email || !password) {
    //         alert('Please fill in both fields.');
    //         return;
    //     }
    
    //     // Send login request to the backend
    //     fetch('/login', {
    //         method: 'POST',
    //         headers: {
    //             'Content-Type': 'application/json'
    //         },
    //         body: JSON.stringify({ email, password })
    //     })
    //     .then(response => {
    //         if (!response.ok) {
    //             return response.json().then(error => { throw new Error(error.message); });
    //         }
    //         return response.json();
    //     })
    //     .then(data => {
    //         if (data.success) {
    //             alert(data.message);
    //             window.location.href = '/';  // Redirect to the home page after login the to profile after profile page is made.
    //         } else {
    //             alert('Login failed: ' + data.message);
    //         }
    //     })
    //     .catch(error => {
    //         console.error('Error:', error);
    //         alert('Login failed: ' + error.message);
    //     });
    // });
    


    // Report form submission
    // document.getElementById("reportForm").addEventListener("submit", function(event) {
    //     event.preventDefault();
        
    //     let formData = new FormData(this);

    //     // Capture form data
    //     let age = document.getElementById("age").value;
    //     let temperature = document.getElementById("temperature").value;
    //     let symptom1 = document.getElementById("symptom1").value;
    //     let symptom2 = document.getElementById("symptom2").value;
    //     let symptom3 = document.getElementById("symptom3").value;
    //     let description = document.getElementById("description").value;
    //     // Create data object
    //     let data = {
    //         age: age,
    //         temperature: temperature,
    //         symptom1: symptom1,
    //         symptom2: symptom2,
    //         symptom3: symptom3,
    //         description: description,
    //         image: image
    //     };

    //     // Send data to the Flask backend
    //     fetch("/predict", {
    //         method: "POST",
    //         body: formData,
    //         headers: {
    //             "Content-Type": "application/json"
    //         },
    //         body: JSON.stringify(data)
    //     })
    //     .then(response => response.json())
    //     .then(data => {
    //         if (data.predicted_disease) {
    //             document.getElementById("result").innerHTML = `<strong>Predicted Disease:</strong> ${data.predicted_disease}`;
    //         } else if (data.error) {
    //             document.getElementById("result").innerHTML = `<strong>Error:</strong> ${data.error}`;
    //         }
    //     })
    //     .catch(error => {
    //         document.getElementById("result").innerHTML = `<strong>Error:</strong> ${error}`;
    //     });
    // });
        
   

    // Video call form submission
    document.getElementById('videoCallForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const vet = document.getElementById('vet').value;

        // Logic for starting a video call
        alert(`Starting a video call with ${vet}`);
        // Implement the actual video call logic here
    });
});

