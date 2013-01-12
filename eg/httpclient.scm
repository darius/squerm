(define (main)
  (url-fetch "wry.me" 80 "/"))

(define (url-fetch host port path)
  (mlet ((conn? conn!) (sprout))
    (tcp-connect conn! (list host port) complaining-keeper)
    (let ((sock! (conn?)))
      (send sock! (string-append "GET " path " HTTP/1.0\r\n\r\n"))
      (let echoing ()
        (let ((m (ask sock! 'read 4096)))
          (cond ((equal? m 'eof) 'ok)
                ((string? m)
                 (write-string m)
                 (echoing))))))))

(define (ask server! tag message)
  (mlet ((? !) (sprout))
    (server! (list tag message !))
    (?)))

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
