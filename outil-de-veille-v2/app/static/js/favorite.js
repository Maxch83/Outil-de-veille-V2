document.addEventListener('DOMContentLoaded', function() {
    // Action pour le bouton qui supprime tous les favoris
    document.getElementById('remove-all-favorites').addEventListener('click', function() {
        fetch(`/remove_all_favorites/all`, {
            method: 'POST'
        }).then(response => {
            if (response.ok) {
                console.log('Remove favorite done');
                // Vérifier si l'élément avec l'id 'articles-container' existe sur la page
                const articlesContainer = document.getElementById('articles-container');
                if (articlesContainer) {
                    // Exécuter les fonctions nécessaires depuis main.js
                    fetchArticlesByFavorites([]);
                }

                // Mettre à null a l'affichage les formulaires de favoris
                document.querySelectorAll('form.custom-select-container').forEach(form => {
                    const favoriteItem = form.querySelector('.select-items div[data-value="None"]');
                    if (favoriteItem) {
                        form.querySelector('.select-selected').innerHTML = favoriteItem.innerHTML;
                        form.querySelector('input[name="selectedItem"]').value = null;
                    }
                });
            } else {
                alert('Failed to remove all favorites');
            }
        });
    });

    // Attacher des événements de clic aux éléments de sélection
    document.querySelectorAll('.select-selected').forEach(selectedElement => {
        selectedElement.addEventListener('click', function() {
            // Fermer toutes les listes déroulantes ouvertes
            document.querySelectorAll('.select-items').forEach(items => {
                items.style.display = 'none';
            });

            // Ouvrir ou fermer la liste déroulante cliquée
            var items = this.nextElementSibling;
            items.style.display = items.style.display === 'flex' ? 'none' : 'flex';
        });
    });

    // Gérer les clics sur les éléments de la liste
    document.querySelectorAll('.select-items div').forEach(function(item) {
        item.addEventListener('click', function() {
            var form = this.closest('form');
            form.querySelector('.select-selected').innerHTML = this.innerHTML;
            var selectedItem = this.getAttribute('data-value');
            form.querySelector('input[name="selectedItem"]').value = selectedItem;
            this.parentElement.style.display = null;
            
            // Send the selected favorite to the server immediately
            fetch('/update_article_favorite', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    favorite_id: selectedItem || null, 
                    article_id: form.dataset.articleId 
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                        // Met à jour l'affichage
                        form.querySelector('.select-selected').innerHTML = data.updated_favorite_icon;
                        // Vérifier si l'élément avec l'id 'articles-container' existe sur la page
                        const articlesContainer = document.getElementById('articles-container');
                        if (articlesContainer) {
                            // Met à jour l'affichage depuis display_favorite.js
                            fetchArticlesByFavorites([]);
                        }
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

    // Fermer toutes les listes déroulantes lorsque l'utilisateur clique en dehors
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.custom-select-container')) {
            document.querySelectorAll('.select-items').forEach(function(items) {
                items.style.display = null;
            });
        }
    });
});