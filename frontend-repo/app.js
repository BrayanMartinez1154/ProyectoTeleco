document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const messageDiv = document.getElementById('responseMessage'); 

    const username = usernameInput.value;
    const password = passwordInput.value;

    if (!username || !password) {
        messageDiv.textContent = 'Por favor, ingresa el usuario y la contraseña.';
        messageDiv.className = 'error';
        return;
    }

    messageDiv.textContent = 'Enviando...';
    messageDiv.className = '';

    const backendUrl = 'https://parcial-backend-haaac3ekfubchad3.canadacentral-01.azurewebsites.net/login';

    try {
        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                usuario: username,
                contrasena: password
            }),
        });

        if (response.ok) {
            const result = await response.json(); // O response.text() si el backend no devuelve JSON
            messageDiv.textContent = result.mensaje || 'Inicio de sesión registrado con éxito.';
            messageDiv.className = 'success';
        } else {
            let errorMessage = `Error: ${response.status} - ${response.statusText}`;
            try {
                const errorResult = await response.json();
                if (errorResult && errorResult.mensaje) {
                    errorMessage = errorResult.mensaje;
                }
            } catch (e) {
                console.warn("No se pudo parsear la respuesta de error como JSON:", e);
            }
            messageDiv.textContent = `Error al enviar los datos. ${errorMessage}`;
            messageDiv.className = 'error';
        }
    } catch (error) {
        console.error('Error en la petición fetch:', error);
        messageDiv.textContent = 'Error de conexión con el servidor. Verifica la URL del backend y tu conexión a internet.';
        messageDiv.className = 'error';
    }
});