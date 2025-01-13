document.addEventListener("DOMContentLoaded", function() {
    const buttons = document.querySelectorAll('.notification-button');
    const links = document.querySelectorAll('a[id^="article-"]');
    const splittext = document.querySelectorAll('.attaquesplit');

    // Remove all notifications
    document.getElementById('remove-all-notifications').addEventListener('click', function() {
        fetch(`/hide_all_notifications/all`, {
            method: 'POST'
        }).then(response => {
            if (response.ok) {
                console.log('Hide all notifications done');
                links.forEach(link => link.style.fontWeight = 'normal');
                buttons.forEach(button => button.remove());
            } else {
                alert('Échec de la suppression de toute les notifications');
            }
        });
    });

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

    function addSpaceToLongWords(htmlText) {
        // Expression régulière pour détecter une chaîne de 24 caractères consécutifs sans espace
        const regex = /(\S{24})/g;
    
        // Remplacement de chaque correspondance par la chaîne trouvée suivie d'un espace
        const updatedText = htmlText.replace(regex, '$1 ');
    
        return updatedText;
    }

    splittext.forEach(element => {
        // Récupère le contenu HTML de chaque élément
        let htmlContent = element.innerHTML;

        // Ajoute un espace après les longues séquences de caractères
        htmlContent = addSpaceToLongWords(htmlContent);

        // Met à jour le contenu HTML de l'élément
        element.innerHTML = htmlContent;
    });
});