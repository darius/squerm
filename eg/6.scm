(define (main)
  (call-with-channel
   (lambda (t-? t-!)
     (let ((dict! (sprout-spawn complaining-keeper (make-dict-process t-!))))
       (let ((kill-dict! (t-?)))
         (print (call dict! '(get hello)))
         (dict! '(#f (put color red)))
         (print (call dict! '(get color)))
         (kill-dict! #t)
         (print (call dict! '(get color))))))))

(define (make-dict-process t-!)
  (lambda (? !)
    (call-with-channel
     (lambda (kill-? kill-!)
       (t-! kill-!)
       (let loop ((table '()))
         (choose
          (list (list kill-? (lambda (_) (print "dict killed")))
                (list ? (lambda (m)
                          (let ((return! (car m))
                                (command (cadr m)))
                            (case (car command)
                              ((get)
                               (return! (look-up (cadr command) table))
                               (loop table))
                              ((put)
                               (loop (acons (cadr command)
                                            (caddr command)
                                            table))))))))))))))

(define (look-up key a-list)
  (cond ((assoc key a-list) => cadr)
        (else #f)))

(define (acons key value a-list)
  (cons (list key value) a-list))

(define (sprout-spawn keeper fn)
  (let ((pair (sprout)))
    (let ((initial-? (car pair))
          (initial-! (cadr pair)))
      (spawn keeper (lambda ()
                      (let ((pair (sprout)))
                        (let ((? (car pair))
                              (! (cadr pair)))
                          (initial-! !)
                          (fn ? !)))))
      (initial-?))))

(define (call-with-channel f)
  (let ((pair (sprout)))
    (f (car pair) (cadr pair))))

(define (call server! message)
  (call-with-channel
   (lambda (? !)
     (server! (list ! message))
     (?))))
