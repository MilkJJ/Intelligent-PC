
document.addEventListener("DOMContentLoaded", function () {
    const chatbotFrame = document.getElementById("chatbot-frame");
    const openChatbotButton = document.getElementById("open-chatbot");
    const closeChatbotButton = document.getElementById("close-chatbot");

    openChatbotButton.addEventListener("click", function () {
        chatbotFrame.style.display = "block";
        openChatbotButton.style.display = "none";
    });

    closeChatbotButton.addEventListener("click", function () {
        chatbotFrame.style.display = "none";
        openChatbotButton.style.display = "block";
        chatbotFrame.querySelector("iframe").contentWindow.postMessage("chatbot-closed", "*");
    });

    window.addEventListener("message", function (event) {
        if (event.data === "chatbot-closed") {
            chatbotFrame.style.display = "none";
            openChatbotButton.style.display = "block";
        }
    });
});