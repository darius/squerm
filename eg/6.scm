(define (main)
  (mlet ((t-? t-!) (sprout))
    (let ((dict! (sprout-spawn complaining-keeper (make-dict-process t-!))))
      (let ((kill-dict! (t-?)))
        (print (call dict! '(get hello)))
        (dict! '(#f (put color red)))
        (print (call dict! '(get color)))
        (kill-dict! #t)
        (print (call dict! '(get color)))))))

(define (make-dict-process t-!)
  (lambda (? !)
    (mlet ((kill-? kill-!) (sprout))
      (t-! kill-!)
      (let loop ((table '()))
        (choose
         (list (list kill-? (lambda (_) (print "dict killed")))
               (list ? (mlambda
                        ((return! ('get key))
                         (return! (look-up key table))
                         (loop table))
                        ((_ ('put key value))
                         (loop (acons key value table)))))))))))

(define (look-up key a-list)
  (cond ((assoc key a-list) => cadr)
        (else #f)))

(define (acons key value a-list)
  (cons (list key value) a-list))

(define (sprout-spawn keeper fn)
  (mlet ((initial-? initial-!) (sprout))
    (spawn keeper (lambda ()
                    (mlet ((? !) (sprout))
                      (initial-! !)
                      (fn ? !))))
    (initial-?)))

(define (call server! message)
  (mlet ((? !) (sprout))
    (server! (list ! message))
    (?)))
