/* A simple server in the internet domain using TCP
   The port number is passed as an argument */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netinet/in.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>

void woops(void){
    printf("[-] Program has exited and is no longer doing stuff!\n\t...just so you know...\n");
    exit(1);
}

void handle(int a){
	printf("Caught CTRL-c event. Closing program...\n");
	exit(0);
}


void error(const char *msg)
{
    /* prints error messages and exits*/
    perror(msg);
    exit(1);
}

int run(int portno)
{
    /* function for handling connections*/

    // Initializes variables
    int rc = 0;
    int sockfd, newsockfd;
    socklen_t clilen;
    char buffer[256];
    char addr[INET_ADDRSTRLEN];
    struct sockaddr_in serv_addr, cli_addr;
    int n;


    // initialize socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);

    if (sockfd < 0) 
       error("[-] ERROR opening socket");
    
    // zero out memory for the server address 
    bzero((char *) &serv_addr, sizeof(serv_addr));
 
    
    // initialize socket struct
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);

    if (bind(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
        error("[-] ERROR on binding");
    
    // listen for connections
    listen(sockfd,256);

    printf("[ ] Listening for client connections on port %d...\n", portno);
    // accepts connection from client
    clilen = sizeof(cli_addr);
    newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
    
    // gets string of connected client's address
    inet_ntop(AF_INET, &(cli_addr.sin_addr), addr, INET_ADDRSTRLEN);
    printf("[+] Got client connection from address %s\n", addr);

    if (newsockfd < 0) {
        perror("[-] ERROR on accept");
        shutdown(sockfd, SHUT_RDWR);
        close(sockfd);
        return 1;
    }

    int count = 0;
    while(1){
        // zeroes out the text buffer
        bzero(buffer,256);
        
        n = read(newsockfd,buffer,255);

        if (n < 0){
            perror("[-] ERROR reading from socket"); 
            break;
        }
        n = send(newsockfd,"I got your message",18, MSG_NOSIGNAL);
        if (n < 0){
            printf("[i] DC from client\n");
            // catches disconnected clients, no printf to keep console clean
            break;
        }
    }

    // close client socket and parent socket
    rc = shutdown(newsockfd, SHUT_RDWR);
    if (rc < 0) {
        error("ERROR shutting down client socket");
        return 1;
    }
    
    rc = shutdown(sockfd, SHUT_RDWR);
    if (rc < 0) {
        error("ERROR shutting down server socket");
        return 1;
    }

    close(newsockfd);
    close(sockfd);

    return 0; 
}

int main(int argc, char* argv[]){
    if (argc < 2) {
        fprintf(stderr,"[-] ERROR, no port provided\n");
        exit(1);
    }

    atexit(woops);
    // initializes signal handlers
	struct sigaction sigIntHandler;
	struct sigaction sigTermHandler;


	sigIntHandler.sa_handler = handle;
   	sigemptyset(&sigIntHandler.sa_mask);
   	sigIntHandler.sa_flags = 0;

	sigTermHandler.sa_handler = handle;
	sigemptyset(&sigTermHandler.sa_mask);
	sigTermHandler.sa_flags = 0;

   	sigaction(SIGINT, &sigIntHandler, NULL);
	sigaction(SIGTERM, &sigTermHandler, NULL);


    // converts passed string int to actual integer
    int portno = atoi(argv[1]);

    int rc = 0;
    int count = 0;

    while(1){
        rc = run(portno);
        if (rc != 0)
        {
            printf("Woops! Looks like something went wrong!\n\tCount value: %d\n", count);
            return 1;
        }
        count++;   
    }
    return 0;

}
