(define (main)
  (with-new-channel
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
    (with-new-channel
     (lambda (kill-? kill-!)
       (t-! kill-!)
       (let loop ((table '()))
         (choose
          (list (list kill-? (lambda (_) (print "dict killed")))
                (list ? (mlambda
                         ((return! ('get key))
                          (return! (look-up key table))
                          (loop table))
                         ((_ ('put key value))
                          (loop (acons key value table))))))))))))

(define (look-up key a-list)
  (cond ((assoc key a-list) => cadr)
        (else #f)))

(define (acons key value a-list)
  (cons (list key value) a-list))

(define (sprout-spawn keeper fn)
  (with-new-channel
   (lambda (initial-? initial-!)
     (spawn keeper (lambda ()
                     (with-new-channel
                      (lambda (? !)
                        (initial-! !)
                        (fn ? !)))))
     (initial-?))))

(define (with-new-channel f)
  (let ((pair (sprout)))
    (f (car pair) (cadr pair))))

(define (call server! message)
  (with-new-channel
   (lambda (? !)
     (server! (list ! message))
     (?))))
