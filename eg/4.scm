(define (main)
  (let ((keeper! (sprout-spawn #f keeper)))
    (sprout-spawn keeper!
                  (lambda (? !)
                    (print 'hello)
                    whee))
    (sprout-spawn keeper!
                  (lambda (? !)
                    (print "I am OK, though")
                    (print 'hurray!)))))

(define (keeper ? !)
  (let loop ()
    (print (?))
    (loop)))

(define (sprout-spawn keeper fn)
  (mlet ((initial-? initial-!) (sprout))
    (spawn keeper (lambda ()
                    (mlet ((? !) (sprout))
                      (initial-! !)
                      (fn ? !))))
    (initial-?)))
