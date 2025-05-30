(url, method, requestData, user_headers) => {
    return new Promise((resolve, reject) => {
        const options = {
            method: method,
            headers: user_headers,
            body: requestData !== null ? JSON.stringify(requestData) : undefined,
            credentials: 'include' // Include cookies in the request
        };
        
        fetch(url, options)
        .then(response => {
            const response_headers = {};
            response.headers.forEach((value, name) => {
                response_headers[name] = value;
            });
            
            return response.text().then(data => {
                resolve({
                    status: response.status,
                    headers: response_headers,
                    data: data
                });
            });
        })
        .catch(error => {
            // Детальное логирование ошибки
            const errorDetails = {
                name: error.name,
                message: error.message,
                stack: error.stack,
                code: error.code,
                errno: error.errno,
                syscall: error.syscall,
                hostname: error.hostname,
                type: Object.prototype.toString.call(error),
                cause: error.cause
            };
            
            console.log('=== DETAILED FETCH ERROR ===');
            console.log('Error object:', error);
            console.log('Error details:', errorDetails);
            console.log('Error keys:', Object.keys(error));
            console.log('Error constructor:', error.constructor.name);
            console.log('=============================');
            
            // Возвращаем ошибку как обычный response вместо исключения
            resolve({
                status: 0,  // специальный статус для network error
                headers: {},
                data: `${error.name}: ${error.message}`,
                networkError: true,
                errorDetails: errorDetails
            });
        });
    });
}