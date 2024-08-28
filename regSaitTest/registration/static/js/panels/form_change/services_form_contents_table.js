document.addEventListener("DOMContentLoaded", function() {
    var serviceId = document.getElementById('service_id').value;
    var tableContainer = document.getElementById('panels_form_services_contents_table');
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    function loadServiceFiles(serviceId) {
        fetch(`/ajax/get-service-contents/${serviceId}/`, {
            method: 'GET',
        })
        .then(response => response.json())
        .then(data => {
            var contents = data.contents;

            var table = document.querySelector('#service-files-table');
            if (!table) {
                table = document.createElement('table');
                table.setAttribute('id', 'service-files-table');
                table.setAttribute('border', '1');
                table.setAttribute('width', '100%');
                tableContainer.parentNode.insertBefore(table, tableContainer);

                var thead = document.createElement('thead');
                var headerRow = document.createElement('tr');
                var headers = ['Filename', 'Filepath', 'Actions'];

                headers.forEach(function(headerText) {
                    var th = document.createElement('th');
                    th.appendChild(document.createTextNode(headerText));
                    headerRow.appendChild(th);
                });

                thead.appendChild(headerRow);
                table.appendChild(thead);
            }

            var tbody = table.querySelector('tbody');
            if (tbody) {
                tbody.innerHTML = '';
            } else {
                tbody = document.createElement('tbody');
                table.appendChild(tbody);
            }

            contents.forEach(function(item) {
                var tr = document.createElement('tr');

                var filenameTd = document.createElement('td');
                filenameTd.appendChild(document.createTextNode(item.filename || 'N/A'));
                tr.appendChild(filenameTd);

                var filepathTd = document.createElement('td');
                filepathTd.appendChild(document.createTextNode(item.filepath || 'N/A'));
                tr.appendChild(filepathTd);

                var actionsTd = document.createElement('td');
                var deleteButton = document.createElement('button');
                deleteButton.textContent = 'Delete';
                deleteButton.addEventListener('click', function(event) {
                    event.preventDefault();
                    deleteFile(item.filepath);
                });
                actionsTd.appendChild(deleteButton);
                tr.appendChild(actionsTd);

                tbody.appendChild(tr);
            });
        })
        .catch(error => console.error('Error:', error));
    }

    function deleteFile(filepath) {
        fetch(`/ajax/delete-service-content/${serviceId}/?filepath=${filepath}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadServiceFiles(serviceId);
            } else {
                alert('Error deleting file.');
            }
        })
        .catch(error => console.error('Error:', error));
    }

    loadServiceFiles(serviceId);
});
