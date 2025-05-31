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
                // Возвращаем объект успешного ответа
                resolve({
                    success: true,
                    response: {
                        status: response.status,
                        headers: response_headers,
                        data: data
                    }
                });
            });
        })
        .catch(error => {
            // Собираем только существующие свойства ошибки
            const errorDetails = {};
            
            // Основные свойства Error объекта
            if (error.name !== undefined) errorDetails.name = error.name;
            if (error.message !== undefined) errorDetails.message = error.message;
            if (error.stack !== undefined && error.stack !== '') errorDetails.stack = error.stack;
            
            // Node.js специфичные свойства (обычно отсутствуют в браузере)
            if (error.code !== undefined) errorDetails.code = error.code;
            if (error.errno !== undefined) errorDetails.errno = error.errno;
            if (error.syscall !== undefined) errorDetails.syscall = error.syscall;
            if (error.hostname !== undefined) errorDetails.hostname = error.hostname;
            
            // Дополнительные свойства
            if (error.cause !== undefined) errorDetails.cause = error.cause;
            if (error.fileName !== undefined) errorDetails.fileName = error.fileName;
            if (error.lineNumber !== undefined) errorDetails.lineNumber = error.lineNumber;
            if (error.columnNumber !== undefined) errorDetails.columnNumber = error.columnNumber;
            
            // Метаинформация
            errorDetails.type = Object.prototype.toString.call(error);
            errorDetails.constructor = error.constructor.name;
            errorDetails.availableKeys = Object.keys(error);
            
            // Возвращаем объект ошибки отдельно от response
            resolve({
                success: false,
                error: {
                    name: error.name,
                    message: error.message,
                    details: errorDetails,
                    timestamp: new Date().toISOString()
                }
            });
        });
    });
}