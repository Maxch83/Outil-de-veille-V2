document.addEventListener("DOMContentLoaded", function() {
    const categories = ['domaines_ioc', 'attaques', 'actualites', 'bulletins'];
    let displayedArticleIds = new Set();  // Set pour stocker les IDs des articles déjà affichés
    let isplayed = false;

    function playNotificationSound() {
        const sound = localStorage.getItem('notificationSound') || 'audio-1.mp3';
        const audio = new Audio(`/static/audio/${sound}`);
        audio.play();
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        const day = String(date.getUTCDate()).padStart(2, '0');
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const year = date.getUTCFullYear();
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');
        return `${day}-${month}-${year} ${hours}:${minutes}`;
    }

    function isToday(dateString) {
        const today = new Date();
        const date = new Date(dateString);
        return date.getUTCDate() === today.getUTCDate() &&
            date.getUTCMonth() === today.getUTCMonth() &&
            date.getUTCFullYear() === today.getUTCFullYear();
    }

    function isOlderThan14Days(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        const timeDiff = today.getTime() - date.getTime();
        const daysDiff = timeDiff / (1000 * 3600 * 24);
        return daysDiff > 14;
    }

    function fetchNews() {
        isplayed = false;
        fetch(`/news/all/json`)
            .then(response => response.json())
            .then(data => {
                categories.forEach(category => {
                    const articles = data[category] || [];
                    const newsList = document.getElementById(`news-list-${category}`);
                    newsList.innerHTML = "";
                    articles.forEach(article => {
                        const listItem = document.createElement('li');
                        listItem.classList.add('list-group-item', 'm-0', 'p-1');

                        const rowDiv = document.createElement('div');
                        rowDiv.classList.add('row');
                        if(newsList.id === 'news-list-attaques' || newsList.id === 'news-list-domaines_ioc'){
                            rowDiv.style.width = '104%';
                        } else {
                            rowDiv.style.width = '102%';
                        }
                        listItem.appendChild(rowDiv);

                        const firstElement = document.createElement('p');
                        if(newsList.id === 'news-list-attaques') {
                            firstElement.classList.add('col-3');
                        } else if(newsList.id === 'news-list-domaines_ioc') {
                            firstElement.classList.add('col-4');
                        } else {
                            firstElement.classList.add('col-2');
                        }

                        const formattedDate = formatDate(article.published);
                        const [datePart, timePart] = formattedDate.split(' ');
                        const dateText = document.createTextNode(datePart);
                        const br = document.createElement('br');
                        const timeText = document.createTextNode(timePart);

                        if (isToday(article.published)) {
                            firstElement.style.fontWeight = 'bold';
                        }

                        firstElement.appendChild(dateText);
                        firstElement.appendChild(br);
                        firstElement.appendChild(timeText);
                        rowDiv.appendChild(firstElement);

                        const SecondElement = document.createElement('a');
                        if(newsList.id === 'news-list-attaques'){
                            SecondElement.href = 'https://www.google.com/search?q='+article.title;
                            SecondElement.setAttribute('target', '_blank');
                            SecondElement.classList.add('col-5', 'nocolor', 'dark-bold');
                        } else if(newsList.id === 'news-list-bulletins'){
                            SecondElement.href = article.link;
                            SecondElement.setAttribute('target', '_blank');
                            if(article.website_title == 'CERT-FR'){
                                SecondElement.classList.add('col-7', 'dark-bold');
                            } else {
                                SecondElement.classList.add('col-7', 'nocolor', 'dark-bold');
                            }
                        } else {
                            SecondElement.href = article.link;
                            SecondElement.setAttribute('target', '_blank');
                            SecondElement.classList.add('col-6', 'nocolor', 'dark-bold');
                        }
                        if (article.show_notification) {
                            SecondElement.style.fontWeight = 'bold';
                        }
                        SecondElement.id = `article-${article.id}`;
                        if(newsList.id === 'news-list-attaques'){
                            SecondElement.innerHTML = addSpaceToLongWords(article.title);
                        } else {
                            SecondElement.innerHTML = article.title;
                        }
                        
                        rowDiv.appendChild(SecondElement);
                        
                        const thirdElement = document.createElement('a');
                        const fourthElement = document.createElement('div');
                        if(newsList.id === 'news-list-actualites') {
                            thirdElement.textContent = article.website_title;
                            thirdElement.classList.add('col-2', 'nocolor');
                            fourthElement.classList.add('col-2', 'd-flex', 'justify-content-end');
                        } else if(newsList.id === 'news-list-attaques'){
                            thirdElement.textContent = article.description;
                            thirdElement.href = article.group_link;
                            thirdElement.setAttribute('target', '_blank');
                            thirdElement.classList.add('col-3', 'attaquant');
                            fourthElement.classList.add('col-1', 'd-flex', 'justify-content-end');
                        } else if(newsList.id === 'news-list-bulletins'){
                            thirdElement.textContent = article.website_title;
                            if(article.website_title == 'CERT-FR'){
                                thirdElement.classList.add('col-2', 'nocolor', 'cert-fr-title');
                            } else if(article.website_title == 'CISA') {
                                thirdElement.classList.add('col-2', 'nocolor', 'cisa-title');
                            } else {
                                thirdElement.classList.add('col-2', 'nocolor');
                            }
                            fourthElement.classList.add('col-1', 'd-flex', 'justify-content-end');
                        } else {
                            thirdElement.textContent = article.website_title;
                            thirdElement.classList.add('col-6', 'nocolor');
                            fourthElement.classList.add('col-2', 'd-flex', 'justify-content-end');
                        }
                        if(newsList.id != 'news-list-domaines_ioc'){
                            rowDiv.appendChild(thirdElement);
                        }
                        rowDiv.appendChild(fourthElement);

                        if (isOlderThan14Days(article.published)) {
                            const buttonHide = document.getElementById(`${article.id}`);
                            fetch(`/hide_notification/${article.id}`, {
                                method: 'POST'
                            }).then(response => {
                                if (response.ok) {
                                    console.log(`Notification for article ${article.id} removed`);
                                    buttonHide.remove();
                                } else {
                                    alert(`Échec de la suppression de la notification de l'article possédant l'id : ${article.id}`);
                                }
                            }).catch(error => {
                                console.error('Error:', error);
                                alert(`Échec de la suppression de la notification de l'article possédant l'id : ${article.id}`);
                            });
                        }

                        if(newsList.id === 'news-list-actualites') {
                            // Formulaire pour sélectionner une catégorie de favori
                            const form = document.createElement('form');
                            form.id = `dropdownForm-${article.id}`;
                            form.action = '/update_favorite';
                            form.method = 'POST';
                            form.classList.add('custom-select-container', 'rtl-dropdown', 'col-11');
                            form.setAttribute('data-article-id', article.id);
                            fourthElement.appendChild(form);

                            // Créer l'input caché
                            const input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = 'selectedItem';
                            input.id = `selectedItem-${article.id}`;
                            input.value = article.favorite_id;
                            form.appendChild(input);

                            // Créer la div select-selected
                            const selectSelected = document.createElement('div');
                            selectSelected.classList.add('select-selected');
                            form.appendChild(selectSelected);

                            // Ajouter l'icône appropriée
                            const icon = document.createElement('i');
                            if(article.favorite_id != null && article.favorite_id != 'None' && article.favorite_id != 'none' && article.favorite_id != 'null') {
                                icon.classList.add('fa-solid', 'fa-bookmark');
                                icon.style.color = article.color;
                            } else {
                                icon.classList.add('empty-bookmark', 'fa-regular', 'fa-bookmark');
                            }
                            selectSelected.appendChild(icon);

                            // Créer la div select-items
                            const selectItems = document.createElement('div');
                            selectItems.classList.add('select-items');
                            form.appendChild(selectItems);

                            // Ajouter l'option par défaut
                            const defaultDivIcon = document.createElement('div');
                            defaultDivIcon.setAttribute('data-value', null);
                            defaultDivIcon.classList.add('favorite-item');
                            selectItems.appendChild(defaultDivIcon);

                            const multipleIcon = document.createElement('i');
                            multipleIcon.classList.add('empty-bookmark', 'fa-regular', 'fa-bookmark');
                            defaultDivIcon.appendChild(multipleIcon);

                            // Ajouter les options de favoris
                            fetch(`/favorites/json`)
                            .then(response => response.json())
                            .then(data => {
                                data.favoris.forEach(favorite => {
                                    const divIcon = document.createElement('div');
                                    divIcon.setAttribute('data-value', favorite.id);
                                    divIcon.classList.add('favorite-item');
                                    selectItems.appendChild(divIcon);

                                    const finalIcon = document.createElement('i');
                                    finalIcon.classList.add('fa-solid', 'fa-bookmark');
                                    finalIcon.style.color = favorite.color;
                                    divIcon.appendChild(finalIcon);
                                });

                                // Initialiser les événements de sélection après avoir ajouté les options
                                initFavoriteForms(form);
                            })
                            .catch(error => {
                                console.error('Error fetching data:', error);
                            });
                        }

                        if (article.show_notification && !isOlderThan14Days(article.published)) {
                            const notification_button = document.createElement('button');
                            notification_button.id = `${article.id}`;
                            notification_button.classList.add('notification-button');
                            if(newsList.id === 'news-list-actualites') {
                                const divNotification = document.createElement('div');
                                divNotification.classList.add('col-1', 'ms-3');
                                fourthElement.appendChild(divNotification);
                                divNotification.appendChild(notification_button);
                            } else {
                                fourthElement.appendChild(notification_button);
                            }

                            if (!displayedArticleIds.has(article.id)) {  // Vérifie si l'article est nouveau
                                if (!isplayed){
                                    playNotificationSound();
                                    isplayed = true;
                                }
                                displayedArticleIds.add(article.id);  // Ajoute l'ID de l'article au Set
                            }

                        } else {
                            const divNotification = document.createElement('div');
                            divNotification.classList.add('col-1');
                            fourthElement.appendChild(divNotification);
                        }

                        newsList.appendChild(listItem);
                    });
                    applyTheme(localStorage.getItem('theme') || 'light');
                    hideNotificationById();
                });
            }).then(() => {
                    const rssLoader = document.getElementById('rss_loader');
                    if (rssLoader) {
                        rssLoader.remove();
                    };
            });
    };

    function hideNotificationById() {
        const buttons = document.querySelectorAll('.notification-button');
        const links = document.querySelectorAll('a[id^="article-"]');
        
        // Fonction pour supprimer la notification
        function removeNotification(articleId) {
            fetch(`/hide_notification/${articleId}`, {
                method: 'POST'
            }).then(response => {
                if (response.ok) {
                    console.log(`Notification for article ${articleId} removed`);
                    var articleElement = document.getElementById('article-' + articleId);
                    if (articleElement) {
                        articleElement.style.fontWeight = 'normal';
                    }
                    var buttonElement = document.getElementById(articleId);
                    if (buttonElement) {
                        buttonElement.remove();
                    }
                } else {
                    alert(`Échec de la suppression de la notification de l'article possédant l'id : ${articleId}`);
                }
            }).catch(error => {
                console.error('Error:', error);
                alert(`Échec de la suppression de la notification de l'article possédant l'id : ${articleId}`);
            });
        }
        // Ajout d'un gestionnaire de clic pour chaque bouton
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                removeNotification(button.id);
            });
        });
        // Ajout d'un gestionnaire de clic pour chaque lien <a>
        links.forEach(link => {
            link.addEventListener('click', function(event) {
                event.preventDefault(); // Empêche la navigation immédiate
                removeNotification(link.id.split('-')[1]); // Passe l'ID de l'article
                window.open(link.href, '_blank'); // Ouvre le lien dans un nouvel onglet
            });
        });
    }

    function initFavoriteForms(form) {
        // Initialiser les formulaires de favoris pour le formulaire spécifique
        form.querySelectorAll('.select-selected').forEach(selectedElement => {
            selectedElement.addEventListener('click', function() {
                var items = this.nextElementSibling;
                items.style.display = items.style.display === 'flex' ? 'none' : 'flex';
            });
        });
    
        form.querySelectorAll('.select-items div').forEach(function(item) {
            item.addEventListener('click', function() {
                var form = this.closest('form');
                form.querySelector('.select-selected').innerHTML = this.innerHTML;
                var selectedItem = this.getAttribute('data-value');
                form.querySelector('input[name="selectedItem"]').value = selectedItem;
                this.parentElement.style.display = 'none';
                
                // Envoyer la sélection au serveur immédiatement
                fetch('/update_article_favorite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        favorite_id: selectedItem, 
                        article_id: form.dataset.articleId 
                    })
                }).then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          // Mettre à jour l'affichage de l'élément sélectionné
                          form.querySelector('.select-selected').innerHTML = data.updated_favorite_icon;
                          applyTheme(localStorage.getItem('theme') || 'light');
                      } else {
                          alert('Failed to update favorite');
                      }
                  })
                  .catch(error => {
                      console.error('Error:', error);
                  });
            });
        });
    
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.custom-select-container')) {
                form.querySelectorAll('.select-items').forEach(function(items) {
                    items.style.display = 'none';
                });
            }
        });
    
        form.querySelectorAll('form.custom-select-container').forEach(function(form) {
            const favoriteValue = form.querySelector('input[name="selectedItem"]').value; // Retrieve the favorite value from a hidden input
            const favoriteItem = form.querySelector(`.select-items div[data-value="${favoriteValue}"]`);
            if (favoriteItem) {
                form.querySelector('.select-selected').innerHTML = favoriteItem.innerHTML;
                form.querySelector('input[name="selectedItem"]').value = favoriteValue;
            }
            form.querySelector('.select-items').style.display = 'none';
        });
    }

    function addSpaceToLongWords(htmlText) {
        // Expression régulière pour détecter une chaîne de 24 caractères consécutifs sans espace
        const regex = /(\S{24})/g;
    
        // Remplacement de chaque correspondance par la chaîne trouvée suivie d'un espace
        const updatedText = htmlText.replace(regex, '$1 ');
    
        return updatedText;
    }

    fetchNews();

    // Récupérer les actualités toutes les 200 secondes (3min20sec)
    setInterval(fetchNews, 200000);
});
