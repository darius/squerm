(define (main)
  (let ((keeper! (spawn #f keeper)))
    (spawn keeper!
           (lambda (? !)
             (print 'hello)
             whee))
    (spawn keeper!
           (lambda (? !)
             (print 'i-am-ok-though)
             (print 'hurray!)))))

(define (keeper ? !)
  (let loop ()
    (print (?))
    (loop)))
