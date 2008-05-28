(define (main)
  (url-fetch "google.com" 80 "/"))

(define (url-fetch host port path)
  (with-new-channel
   (lambda (conn? conn!)
     (tcp-connect conn! (list host port) complaining-keeper)
     (let ((sock! (conn?)))
       (send sock! (string-append "GET " path " HTTP/1.0\r\n\r\n"))
       (let echoing ()
         (let ((m (ask sock! 'read 4096)))
           (cond ((equal? m 'eof) 'ok)
                 ((string? m)
                  (write m)             ;xxx write-string
                  (echoing)))))))))

(define (with-new-channel f)
  (let ((pair (sprout)))
    (f (car pair) (cadr pair))))

(define (ask server! tag message)
  (with-new-channel
   (lambda (? !)
     (server! (list tag message !))
     (?))))

(define (string-append a b c)
  ; XXX hack
  (+ a (+ b c)))

(define (send sock! string)
  (let loop ((s string))
    (if (equal? s "")
        'ok
        (let ((n (ask sock! 'write s)))
          (cond ((= n 0) (exit "socket failure"))
                (else (loop (tail s n))))))))
