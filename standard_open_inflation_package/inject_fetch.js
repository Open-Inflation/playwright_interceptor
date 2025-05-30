(url, method, requestData, user_headers) => {
    return new Promise((resolve, reject) => {
        const options = {
            method: method,
            headers: user_headers,
            body: requestData !== null ? JSON.stringify(requestData) : undefined
        };
        fetch(url, options)
        .then(response => {
            const headers = {};
            response.headers.forEach((value, name) => {
                headers[name] = value;
            });
            return response.text().then(data => {
                resolve({
                    status: response.status,
                    headers: headers,
                    data: data
                });
            });
        })
        .catch(error => reject(error));
    });
}